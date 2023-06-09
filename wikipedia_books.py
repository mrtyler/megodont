#!/usr/bin/env python


import pandas as pd


TARGET_TABLE_COLUMNS = ("Year", "Author", "Novel")
NEBULA_NOVELS_URL = "https://en.wikipedia.org/wiki/Nebula_Award_for_Best_Novel"


def fetch_url(url):
    print(f"Fetching {url}...")
    tables = pd.read_html(url, flavor="bs4")
    return tables


def find_target_table(tables):
    target_table = None
    for table in tables:
        if all([column in table.columns for column in TARGET_TABLE_COLUMNS]):
            target_table = table
            break
    else:
        raise ValueError("Couldn't find target table")
    return target_table


def drop_unwanted_columns(table):
    for column in table.columns:
        if column not in TARGET_TABLE_COLUMNS:
            print(f"Dropping column {column}")
            table = table.drop(column, axis=1)
    return table


def main():
    books = []
    for url in (NEBULA_NOVELS_URL,):
        tables = fetch_url(url)
        table = find_target_table(tables)
        table = drop_unwanted_columns(table)
        num_rows = table.shape[0]

        # Populate new columns
        award_col = ["Nebula" for _ in range(num_rows)]
        table = table.assign(Award=award_col)

        category_col = ["Novel" for _ in range(num_rows)]
        table = table.assign(Category=category_col)

        winner_col = []
        for row in table.iterrows():
            if row[1]["Author"].endswith("*"):
                winner_col.append("Winner")
                # Also modify Author to remove marker
                table.at[row[0], "Author"] = table.at[row[0], "Author"][:-1]
            else:
                winner_col.append("Nominee")
        table = table.assign(Winner=winner_col)


        # Debugggggg printffffffff
        #print("\n".join([f"({row[1]['Year']}) {row[1]['Author']} - {row[1]['Novel']}" for row in table.iterrows() if row[1]["Winner"] != "Winner"]))
        print(table)


if __name__ == "__main__":
    main()
