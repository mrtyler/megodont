#!/usr/bin/env python


# TODO
## combine like books
### author vs author(s) correction
### concating
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
    for row in table.iterrows():
        collected_table = pd.concat([collected_table, row[1]])
    return collected_table


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

        print("Populating final new columns")
        zero_col = [0 for _ in range(num_rows)]
        table = table.assign(Rating=zero_col)
        empty_col = ["" for _ in range(num_rows)]
        table = table.assign(Notes=empty_col)

        # first middle middle* last -> last, first middle middle*
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

        # Combine like entries
        #
        # First time through, there is nothing to do but seed collected_table with the first processed table
        if collected_table is None:
            print("Seeding collected_table with first table")
            collected_table = table
        else:
            print("Folding table into collected_table")
            collected_table = resolve_duplicates(collected_table, table)



        # Debugggggg printffffffff
        #print("\n".join([f"({row[1]['Year']}) {row[1][article["author_column"]]} - {row[1]['Novel']}" for row in table.iterrows() if row[1]["Winner"] != "Winner"]))
        # Debugggggg file writeeee
        #with open(f"{article['award']}.{article['category']}.csv", "w") as ff:
        #    ff.write(table.to_csv())



    #print(collected_table.to_csv())
    with open(f"books.csv", "w") as ff:
        ff.write(collected_table.to_csv())


if __name__ == "__main__":
    main()
