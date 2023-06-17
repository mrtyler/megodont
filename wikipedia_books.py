#!/usr/bin/env python


# TODO
## clean up years [e]
## clean up cixin liu (Chinese) lol
## last, first
## combine like books
## find and fix outliers (thomas m drisch, diff authors of same book, translator things, etc.)
## add novellas lists
## add locus lists? others?


import re

import pandas as pd


ARTICLES = [
###    {
###        "author_column": "Author",
###        "award": "Nebula",
###        "category": "Novel",
###        "target_table_columns": ("Year", "Author", "Novel"),
###        "url": "https://en.wikipedia.org/wiki/Nebula_Award_for_Best_Novel",
###    },
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


def resolve_duplicates(table):
    return table


def main():
    for article in ARTICLES:
        tables = fetch_url(article["url"])
        table = find_target_table(tables, article)
        table = drop_unwanted_columns(table, article)
        num_rows = table.shape[0]

        # Populate new columns
        award_col = [article["award"] for _ in range(num_rows)]
        table = table.assign(Award=award_col)

        category_col = [article["category"] for _ in range(num_rows)]
        table = table.assign(Category=category_col)

        winner_col = []
        for row in table.iterrows():
            if row[1][article["author_column"]].endswith("*"):
                winner_col.append("Winner")
                # Also modify Author to remove marker
                table.at[row[0], article["author_column"]] = table.at[row[0], article["author_column"]][:-1]
            else:
                winner_col.append("Nominee")
        table = table.assign(Winner=winner_col)

### WIP. I don't think this works, and I want to look at DataFrame.replace() anyway.
###        subs = [
###            (re.compile(r"\[\s\+\]$"), r""),
###        ]
###        compiled_subs = [(re.compile(sub[0]), sub[1]) for sub in subs]
###        for row in table.iterrows():
###            for sub in compiled_subs:
###                row[1][article["author_column"]] = sub[0].sub(sub[1], row[1][article["author_column"]])

        table = resolve_duplicates(table)



        # Debugggggg printffffffff
        #print("\n".join([f"({row[1]['Year']}) {row[1][article["author_column"]]} - {row[1]['Novel']}" for row in table.iterrows() if row[1]["Winner"] != "Winner"]))
        print(table.to_csv())


if __name__ == "__main__":
    main()
