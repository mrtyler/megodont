#!/usr/bin/env python


# TODO
## re-fill 0 rating (where is this going? maybe 0 counts as none and gets dropped? anyway)
## don't lose row if i "accidentally" change a key column like author! maybe just how=outer? or will my dumb _x _y logic (that needs revisiting) mess that up?
## revisit dumb _x _y logic in merge_human
## also Year col is in the wrong place again smh
## heh i think all of this should have been collected_table["Significance"] = human_table["Significance"] X 3 columns T.T smh. o wate maybe not because i need to merge to potentially re-sort and everything with new entries and suchhhhh

## check for overlap between categories(?!)

## add novellas lists -- separate file here. cli option? comment-it-out hack aka THE BRENDAN? [brendan is watching dot meme]

## find and fix outliers (thomas m drisch, diff authors of same book, translator things, (also known as) inconsistency [fix wikipedia :)] etc.)
## filter "Not awarded"
## filter first moon is a harsh mistress is what i decided
### maybe also filter dune world for same logic? less impactful but more pure

## column per award i guess. fillna to empty string
## if not, maybe move category back out to its own column (or nowhere if separate sheets)


import os
import re

import pandas as pd


ARTICLES = [
    {
        "author_column": "Author(s)",
        "award": "Hugo",
        "category": "Novel",
        "nominee_score": 4,
        "target_table_columns": ("Year", "Author(s)", "Novel"),
        "title_column": "Novel",
        "url": "https://en.wikipedia.org/wiki/Hugo_Award_for_Best_Novel",
        "winner_score": 10,
    },
    {
        "author_column": "Author",
        "award": "Nebula",
        "category": "Novel",
        "nominee_score": 4,
        "target_table_columns": ("Year", "Author", "Novel"),
        "title_column": "Novel",
        "url": "https://en.wikipedia.org/wiki/Nebula_Award_for_Best_Novel",
        "winner_score": 10,
    },
    {
        "author_column": "Author",
        "award": "Locus",
        "category": "Novel",
        "nominee_score": 0,
        "target_table_columns": ("Year", "Author", "Nominated Work"),
        "title_column": "Nominated Work",
        "url": "https://en.wikipedia.org/wiki/Locus_Award_for_Best_Novel",
        "winner_score": 1,
        "winners_only": True,
    },
    {
        "author_column": "Author",
        "award": "LocSf",
        "category": "Novel",
        "nominee_score": 0,
        "target_table_columns": ("Year", "Author", "Nominated Work[1]"),
        "title_column": "Nominated Work[1]",
        "url": "https://en.wikipedia.org/wiki/Locus_Award_for_Best_Science_Fiction_Novel",
        "winner_score": 1,
        "winners_only": True,
    },
    {
        "author_column": "Author",
        "award": "LocF",
        "category": "Novel",
        "nominee_score": 0,
        "target_table_columns": ("Year", "Author", "Novel"),
        "title_column": "Novel",
        "url": "https://en.wikipedia.org/wiki/Locus_Award_for_Best_Fantasy_Novel",
        "winner_score": 1,
        "winners_only": True,
    },
###    {
###        "author_column": "Author(s)",
###        "award": "Hugo",
###        "category": "N'ella",
###        "nominee_score": 4,
###        "target_table_columns": ("Year", "Author(s)", "Novella"),
###        "title_column": "Novella",
###        "url": "https://en.wikipedia.org/wiki/Hugo_Award_for_Best_Novella",
###        "winner_score": 10,
###    },
###    {
###        "author_column": "Author",
###        "award": "Nebula",
###        "category": "N'ella",
###        "nominee_score": 4,
###        "target_table_columns": ("Year", "Author", "Novella"),
###        "title_column": "Novella",
###        "url": "https://en.wikipedia.org/wiki/Nebula_Award_for_Best_Novella",
###        "winner_score": 10,
###    },
]
HUMAN_GENERATED_CSV = "books - books.csv.csv"

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
    join_columns = [ARTICLES[0]["author_column"], ARTICLES[0]["title_column"]]
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
        "Year_x": 99999,  # Must be > all real years so we can drop it with min() later
        "Significance_x": 0,
        "Awards_x": "",
        "Year_y": 99999,  # Must be > all real years so we can drop it with min() later
        "Significance_y": 0,
        "Awards_y": "",
    }
    new_table = new_table.fillna(value=fill_values)
    # Hugo and Nebula in particular disagree on dates for many books (e.g.
    # Paladin of Souls)
    for column in ("Year",):
        # Use insert() to keep Year as the first column
        new_table.insert(0, column, new_table[f"{column}_x"].astype(int).combine(new_table[f"{column}_y"].astype(int), min))
        new_table = new_table.drop(f"{column}_x", axis=1)
        new_table = new_table.drop(f"{column}_y", axis=1)
    for column in ("Significance", "Awards",):
        new_table[column] = new_table[f"{column}_x"] + new_table[f"{column}_y"]
        new_table = new_table.drop(f"{column}_x", axis=1)
        new_table = new_table.drop(f"{column}_y", axis=1)
    return new_table


def merge_or_init_human_columns(collected_table):
    def init_human_columns(collected_table):
        collected_num_rows = collected_table.shape[0]
        # String "0" because of resolve_duplicates() things
        zero_col = ["0" for _ in range(collected_num_rows)]
        collected_table = collected_table.assign(Rating=zero_col)
        empty_col = ["" for _ in range(collected_num_rows)]
        collected_table = collected_table.assign(WhenRead=empty_col)
        collected_table = collected_table.assign(Notes=empty_col)
        return collected_table

    def merge_human_columns(collected_table):
        human_table = pd.read_csv(HUMAN_GENERATED_CSV)
        join_columns = [ARTICLES[0]["author_column"], ARTICLES[0]["title_column"]]
        merged_table = collected_table.merge(human_table, on=join_columns, how="left")

        # Keep everything from left set, except human columns
        for decorated_column in merged_table.columns:
            column = re.sub(r"_[xy]$", "", decorated_column)
            human_columns = ("Rating", "WhenRead", "Notes",)
            if column in human_columns:
                merged_table[column] = merged_table[f"{column}_y"]
            elif column in join_columns:
                # Nothing to do for undecorated columns i.e. the ones from the join
                continue
            else:
                merged_table[column] = merged_table[f"{column}_x"]
        for decorated_column in merged_table.columns:
            if decorated_column.endswith("_x") or decorated_column.endswith("_y"):
                merged_table = merged_table.drop(decorated_column, axis=1)
        return merged_table

    collected_table = init_human_columns(collected_table)
    if os.path.exists(HUMAN_GENERATED_CSV):
        collected_table = merge_human_columns(collected_table)
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

        # TODO delete this and/or reformat category/awards (column per award, category maybe absent or some overlap thing)
        #print("Populating new columns")
        #award_col = [article["award"] for _ in range(num_rows)]
        #table = table.assign(Award=award_col)
        #category_col = [article["category"] for _ in range(num_rows)]
        #table = table.assign(Category=category_col)

        print("Calculating Winner and Significance")
        winner_col = []
        significance_col = []
        for row in table.iterrows():
            if row[1][article["author_column"]].endswith("*") or article.get("winners_only"):
                winner_col.append(f"{article['award']} Win({article['winner_score']}), ")
                significance_col.append(article["winner_score"])
            else:
                winner_col.append(f"{article['award']} Nom({article['nominee_score']}), ")
                significance_col.append(article["nominee_score"])
        table = table.assign(Awards=winner_col)
        table = table.assign(Significance=significance_col)

        # first middle middle+ last -> last, first middle middle+
        #
        # Weird logic to treat ' (translator)' as part of the last name. Had to
        # add non-'(' to non-space to make it work.
        print("Removing trailing * from author names")
        table = table.replace(
            to_replace={article["author_column"]: r'\*$'},
            value={article["author_column"]: r''},
            regex=True,
        )
        print("Changing author names to last, first")
        table = table.replace(
            to_replace={article["author_column"]: r'(.*) ([^ (]+( \(translator\))?)'},
            value={article["author_column"]: r'\2, \1'},
            regex=True,
        )
        # Special case: Ursula K. Le Guin
        table = table.replace(
            to_replace={article["author_column"]: "Guin, Ursula K. Le",},
            value={article["author_column"]: "Le Guin, Ursula K.",},
        )

        print("Normalizing author and title column names")
        table = table.rename(columns={
            article["author_column"]: ARTICLES[0]["author_column"],
            article["title_column"]: ARTICLES[0]["title_column"],
        })

        # Combine like entries
        #
        # First time through, there is nothing to do but seed collected_table with the first processed table
        if collected_table is None:
            print("Seeding collected_table with first table")
            collected_table = table
        else:
            print("Folding table into collected_table")
            collected_table = resolve_duplicates(collected_table, table)

    print("Final cleanup")
    collected_table = collected_table.replace(to_replace={"Awards": r", $"}, value={"Awards": r""}, regex=True)
    collected_table["Significance"] = collected_table["Significance"].astype(int)

    print("Populating human-filled columns")
    collected_table = merge_or_init_human_columns(collected_table)

    # Sort it out
    print("Sorting data")
    collected_table = collected_table.sort_values(by=["Year"],)
    collected_table = collected_table.sort_values(by=["Significance", "Awards"], ascending=False)

    # Write it down
    print("Writing csv")
    #print(collected_table.to_csv())
    with open(f"books.csv", "w") as ff:
        ff.write(collected_table.to_csv(index=False))


if __name__ == "__main__":
    main()
