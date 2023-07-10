#!/usr/bin/env python


# TODO
## hugo first because hugo was first

## better/different solution for combining award/category/winner? (novella is coming, will there be overlap?)

## one off years (diamond age, paladin of souls)
### will have consequences for the moon is a harsh mistress hugo double-dip (dune world/dune similar but name isn't the same so slightly different less impactful problem)
## find and fix outliers (thomas m drisch, diff authors of same book, translator things, etc.)

## add novellas lists
## add locus lists? others?


import re

import pandas as pd


ARTICLES = [
    {
        "author_column": "Author",
        "award": "Nebula",
        "category": "Novel",
        "target_table_columns": ("Year", "Author", "Novel"),
        "url": "https://en.wikipedia.org/wiki/Nebula_Award_for_Best_Novel",
    },
    {
        "author_column": "Author(s)",
        "award": "Hugo",
        "category": "Novel",
        "target_table_columns": ("Year", "Author(s)", "Novel"),
        "url": "https://en.wikipedia.org/wiki/Hugo_Award_for_Best_Novel",
    },
]


def fetch_url(url):
    print(f"Fetching {url}...")
    tables = pd.read_html(url, flavor="bs4")
    return tables


def find_target_table(tables, article):
    target_table = None
    for table in tables:
        if all([column in table.columns for column in article["target_table_columns"]]):
            target_table = table
            break
    else:
        raise ValueError("Couldn't find target table")
    return target_table


def drop_unwanted_columns(table, article):
    for column in table.columns:
        if column not in article["target_table_columns"]:
            print(f"Dropping column {column}")
            table = table.drop(column, axis=1)
    return table


def resolve_duplicates(collected_table, table):
    # Workaround for "ValueError: You are trying to merge on int64 and object
    # columns. If you wish to proceed you should use pd.concat" from
    # https://stackoverflow.com/questions/64385747/valueerror-you-are-trying-to-merge-on-object-and-int64-columns-when-use-pandas
    for tt in (collected_table, table):
        tt["Year"] = tt["Year"].astype(str)
    join_columns = ["Year", "Author", "Novel", "Category"]
    new_table = pd.merge(
        collected_table,
        table,
        on=join_columns,
        how="outer",
    )
    # merge() leaves NaN for items that don't appear in both lists. Fill with
    # sensible defaults so later concatenation makes sense (and doesn't result
    # in NaN everywhere)
    fill_values = {
        "Significance_x": 0,
        "Award_x": "",
        "Winner_x": "",
        "Significance_y": 0,
        "Award_y": "",
        "Winner_y": "",
    }
    new_table = new_table.fillna(value=fill_values)
    for column in ("Significance", "Award", "Winner"):
        new_table[column] = new_table[f"{column}_x"] + new_table[f"{column}_y"]
        new_table = new_table.drop(f"{column}_x", axis=1)
        new_table = new_table.drop(f"{column}_y", axis=1)
    return new_table


def main():
    collected_table = None
    for article in ARTICLES:
        tables = fetch_url(article["url"])
        table = find_target_table(tables, article)
        num_rows = table.shape[0]

        table = drop_unwanted_columns(table, article)

        print("Cleaning up text")
        # Cixin Liu (Chinese) [lol]
        table = table.replace(to_replace=r" \(Chinese\)", value="", regex=True)
        # Jean Bruller (French) [lol]
        table = table.replace(to_replace=r" \(French\)", value="", regex=True)
        # 2015[e] -> 2015
        table = table.replace(to_replace=r"\[[a-z]\]", value="", regex=True)

        print("Populating new columns")
        award_col = [article["award"] for _ in range(num_rows)]
        table = table.assign(Award=award_col)
        category_col = [article["category"] for _ in range(num_rows)]
        table = table.assign(Category=category_col)

        print("Calculating Winner and Significance")
        winner_col = []
        significance_col = []
        for row in table.iterrows():
            if row[1][article["author_column"]].endswith("*"):
                winner_col.append("Winner")
                # Also modify Author to remove marker
                table.at[row[0], article["author_column"]] = table.at[row[0], article["author_column"]][:-1]
                significance_col.append(5)
            else:
                winner_col.append("Nominee")
                significance_col.append(2)
        table = table.assign(Winner=winner_col)
        table = table.assign(Significance=significance_col)

        # first middle middle+ last -> last, first middle middle+
        #
        # Do this after special \* processing for winner
        #
        # Weird logic to treat ' (translator)' as part of the last name. Had to
        # add non-'(' to non-space to make it work.
        print("Changing author names to last, first")
        table = table.replace(
            to_replace={article["author_column"]: r'(.*) ([^ (]+( \(translator\))?)'},
            value={article["author_column"]: r'\2, \1'},
            regex=True,
        )
        # Special case: Ursula K. Le Guin
        table = table.replace("Guin, Ursula K. Le", "Le Guin, Ursula K.")

        print("Renaming author column")
        table = table.rename(columns={article["author_column"]: ARTICLES[0]["author_column"]})

        # Combine like entries
        #
        # First time through, there is nothing to do but seed collected_table with the first processed table
        if collected_table is None:
            print("Seeding collected_table with first table")
            collected_table = table
        else:
            print("Folding table into collected_table")
            collected_table = resolve_duplicates(collected_table, table)

    print("Populating final new columns")
    collected_num_rows = collected_table.shape[0]
    # String "0" because of resolve_duplicates() things
    zero_col = ["0" for _ in range(collected_num_rows)]
    collected_table = collected_table.assign(Rating=zero_col)
    empty_col = ["" for _ in range(collected_num_rows)]
    collected_table = collected_table.assign(WhenRead=empty_col)
    collected_table = collected_table.assign(Notes=empty_col)

    # Sort it out
    #
    # Handle year separately because we want oldest first (but other stuff is reverse sorted)
    collected_table = collected_table.sort_values(
        by=["Year"],
    )
    sort_cols = [
        "Significance",
        "Award",
    ]
    collected_table = collected_table.sort_values(
        by=sort_cols,
        ascending=False,
    )

    #print(collected_table.to_csv())
    with open(f"books.csv", "w") as ff:
        ff.write(collected_table.to_csv(index=False))


if __name__ == "__main__":
    main()
