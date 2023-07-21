#!/usr/bin/env python


# TODO

## NOTE! As of 2023-07-17, there is no overlap between Hugo/Nebula Novel/Novellas and Locus Novels.
## But there IS overlap between Nebula Novel and Locus Novella -- not sure how I'm going to handle this :O :
## 1997.0,"Willis, Connie",Bellwether,5.0,"Nebula Novel Nom(4), Locus N'ella Win(1)",0.0,,
## 1996.0,"Willis, Connie",Remake,5.0,"Hugo Novel Nom(4), Locus N'ella Win(1)",0.0,,
##
## Relatedly, not sure what to do about Category given this overlap.
### Separate .csv file? Separate .xlsx worksheet (eventually)? CLI option to specify behavior? Comment-it-out hack aka THE BRENDAN?

## NOTE! As of 2023-07-17, I fixed inconsistencies in the wikipedia Hugo and Nebula lists for the same title:
## XXX not yet 1. Thomas Disch should be Thomas M. Disch, as he is listed elsewhere on wikipedia and at e.g. https://www.thehugoawards.org/hugo-history/1981-hugo-awards/
## XXX not yet 2. Change Nebula listing "Ursula Vernon (as T. Kingfisher)" to match Hugo which has "T. Kingfisher" that links to https://en.wikipedia.org/wiki/Ursula_Vernon. This is consistent with how she is credited at https://nebulas.sfwa.org/award-year/2022/

## rename Novel etc. columns at the end to Title
### ...by extracting fINAL_AUTHOR_COLUMN_NAME / TITLE and replacing all the goofy hardcoded ARTICLES[0]

## column per award i guess. fillna to empty string
## if not, maybe move category back out to its own column (or nowhere if separate sheets)
## thinking of more complicated thing to make spreadsheeting easier: column per award, value is number of points. so uh i guess Hugo (4/10): 4, Nebula (4/10): 10, LocSF (0/1): 1. i think csv will still do calculation and fill in real Significance, but this opens door for spreadsheet-level customization where Signif col can be =sum(a7:a9) instead

## add retro-hugos?
## add other awards??

## threads for wikipedia fetches
### retries for wikipedia fetches?
## caches for wikipedia fetches (invalidation seems hard so maybe a --clean option?)

## generate .xlsx? sheet per category. do the formula lookup for Signif myself (maybe on a dedicated sheet because denormalized data lol)

## break main into functions, sergeants/privates
## write some tests for key functionality EL OH EL

## do something different with multiple authors, translators, etc.?


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
    {
        "author_column": "Author(s)",
        "award": "Hugo",
        "category": "N'ella",
        "nominee_score": 4,
        "target_table_columns": ("Year", "Author(s)", "Novella"),
        "title_column": "Novella",
        "url": "https://en.wikipedia.org/wiki/Hugo_Award_for_Best_Novella",
        "winner_score": 10,
    },
    {
        "author_column": "Author",
        "award": "Nebula",
        "category": "N'ella",
        "nominee_score": 4,
        "target_table_columns": ("Year", "Author", "Novella"),
        "title_column": "Novella",
        "url": "https://en.wikipedia.org/wiki/Nebula_Award_for_Best_Novella",
        "winner_score": 10,
    },
    {
        "author_column": "Author",
        "award": "Locus",
        "category": "N'ella",
        "nominee_score": 0,
        "target_table_columns": ("Year", "Author", "Novella"),
        "title_column": "Novella",
        "url": "https://en.wikipedia.org/wiki/Locus_Award_for_Best_Novella",
        "winner_score": 1,
        "winners_only": True,
    },
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

    # Hugo and Nebula in particular have different rules for award dates for
    # many books (e.g. Paladin of Souls). We'll keep the earliest date that we
    # see.
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
        collected_table = collected_table.merge(human_table, on=join_columns, how="outer")

        if any([f"{col}_x" in collected_table.columns or f"{col}_y" in collected_table.columns for col in join_columns]):
            raise ValueError("Eyyyyyyy column mismatch??")

        # Resolve "conflicts" by taking the right (human-generated csv) side
        # for the human-managed columns...
        human_columns = ("Rating", "WhenRead", "Notes",)
        for column in human_columns:
            collected_table[column] = collected_table[f"{column}_y"]
            collected_table = collected_table.drop(f"{column}_x", axis=1)
            collected_table = collected_table.drop(f"{column}_y", axis=1)

        # ...and the left (computer-generated) side for everything else
        for column in collected_table.columns:
            if column.endswith("_x"):
                column_root = re.sub(r"_x$", "", column)
                # Keep "Year" as the first column
                if column_root == "Year":
                    collected_table.insert(0, column_root, collected_table[column])
                # Everything else to the right, but left of human-managed columns
                else:
                    left_of_human_columns_pos = len(collected_table.columns) - len(human_columns)
                    collected_table.insert(left_of_human_columns_pos, column_root, collected_table[column])
                collected_table = collected_table.drop(column, axis=1)
            elif column.endswith("_y"):
                collected_table = collected_table.drop(column, axis=1)
            else:
                # Ignore already-processed column
                pass

        # Re-fill human-managed columns that have non-empty defaults. This is
        # needed for when new rows are added to the computer-generated side (or
        # e.g. if the human-generated csv contains only the few rows with
        # human-generated ratings and not the whole collected corpus).
        fill_values = {
            "Rating": 0,
        }
        collected_table = collected_table.fillna(value=fill_values)

        # Ship it!
        return collected_table

    # Main logic
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
        # Remove footnote links like 2015[e] -> 2015
        table = table.replace(to_replace=r"\[[a-z]\]", value="", regex=True)
        # Cixin Liu (Chinese) [lol]
        table = table.replace(to_replace=r" \(Chinese\)", value="", regex=True)
        # Jean Bruller (French) [lol]
        table = table.replace(to_replace=r" \(French\)", value="", regex=True)
        # Remove leading/ending quotes, as in Novella titles ("Stardance")
        ### hmmmmmm! This had some...unexpected results as the practice of turning a Novella into a Novel of the same name is not uncommon, apparently!
        ### Perhaps I should not worry about the actually fewer cases where the same-titled things are not the same! Separate but equal categories!
        ### This merge did surface some interesting works that would otherwise be buried!
        ### 1992.0,"Kress, Nancy",Beggars in Spain,28.0,"Hugo Novel Nom(4), Nebula Novel Nom(4), Hugo N'ella Win(10), Nebula N'ella Win(10)",0.0,,
        ### 1986.0,"Robinson, Kim Stanley",Green Mars,23.0,"Hugo Novel Win(10), Nebula Novel Nom(4), LocSf Novel Win(1), Hugo N'ella Nom(4), Nebula N'ella Nom(4)",0.0,,
        ### 1983.0,"Brin, David",The Postman,13.0,"Hugo Novel Nom(4), Nebula Novel Nom(4), LocSf Novel Win(1), Hugo N'ella Nom(4)",0.0,,
        ### 1966.0,"Davidson, Avram",Rogue Dragon,8.0,"Nebula Novel Nom(4), Nebula N'ella Nom(4)",0.0,,
        ### 1975.0,"Dozois, Gardner",Strangers,8.0,"Nebula Novel Nom(4), Hugo N'ella Nom(4)",0.0,,
        ### 1982.0,"Palmer, David R.",Emergence,8.0,"Hugo Novel Nom(4), Hugo N'ella Nom(4)",0.0,,
        ### 1987.0,"Flynn, Michael F.",Eifelheim,8.0,"Hugo Novel Nom(4), Hugo N'ella Nom(4)",0.0,,
        ### 1997.0,"Willis, Connie",Bellwether,5.0,"Nebula Novel Nom(4), Locus N'ella Win(1)",0.0,,
        ### 1996.0,"Willis, Connie",Remake,5.0,"Hugo Novel Nom(4), Locus N'ella Win(1)",0.0,,
        table = table.replace(to_replace=r'^"(.*)"$', value=r"\1", regex=True)
        # Drop "(also known as ...)"
        #
        # Consider "Alfred Bester - The Computer Connection (also known as The
        # Indian Giver)". The Hugos
        # (https://www.thehugoawards.org/hugo-history/1976-hugo-awards/) list
        # the alternate title while the Nebulas do not
        # (https://nebulas.sfwa.org/award-year/1975/).
        #
        # The same is true for "Sawyer, Robert J. - The Terminal Experiment
        # (also known as Hobson's Choice)"
        #
        # So the wikipedia articles faithfully represent the underlying awards
        # and are not in need of normalization.
        #
        # I don't love dropping data but it's not sustainable to handle each
        # exception by hand. A TODO-able alternative is to do another merge
        # pass with logic that understands "Foo" and "Foo (also known as Bar)"
        # are the same and we should keep the longer form.
        table = table.replace(to_replace=r' \(also known as .*\)$', value=r"", regex=True)

        print("Dropping rows when no award given")
        # Drop "Not awarded" and variants
        table = table[table[article["author_column"]] != "Not awarded"]
        table = table[table[article["author_column"]] != "(no award)+"]

        # The wikipedia article says, "_The Moon Is a Harsh Mistress_ was
        # serialized in 1965–66, and was allowed to be nominated for both
        # years."
        #
        # That's not helpful for our purposes, so we'll drop the 1966 Hugo
        # Novel Nomination and go with the 1967 Hugo Novel Win (which will
        # later merge with the 1967 Nebula Novel Nomination).
        table = table.drop(
            table[(table[article["title_column"]] == "The Moon Is a Harsh Mistress") & (table["Year"] == "1966")]
            .index
        )

        # Similar to the TMiaHM situation, wikipedia says, "_Dune World_ was
        # the title of the 1964 serialized novel; when "Dune World" and its
        # sequel, "The Prophet of Dune", were incorporated into the 1966
        # edition of _Dune_, the book edition was allowed to be nominated in
        # 1966." dune world
        #
        # This is similarly unhelpful for our purposes, so we'll drop the 1964
        # Hugo Novel Nomination for Dune World and let the spice^W awards flow
        # to the 1966 Hugo/Nebula Novel Wins.
        table = table[table[article["title_column"]] != "Dune World"]

        # There appears to be a similar situation with Katherine MacLean's 1972
        # Nebula Novella Win for "The Missing Man" and her 1976 Nebula Novel
        # Nomination for _Missing Man_. But
        # https://en.wikipedia.org/wiki/Katherine_MacLean says, "[_Missing
        # Man_] is a fix-up of MacLean's three Rescue Squad stories, including
        # the 1971 Nebula Award-winning novella of the same name."
        #
        # The use/non-use of "The" in the title is consistent on wikipedia and
        # goodreads so I'm going to let these go as separate entities with
        # separate stats.
        pass

        print("Calculating Winner and Significance")
        winner_col = []
        significance_col = []
        for row in table.iterrows():
            if row[1][article["author_column"]].endswith("*") or article.get("winners_only"):
                winner_col.append(f"{article['award']} {article['category']} Win({article['winner_score']}), ")
                significance_col.append(article["winner_score"])
            else:
                winner_col.append(f"{article['award']} {article['category']} Nom({article['nominee_score']}), ")
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
    # TODO Only bother with this if it fixes titles like "2312" getting parsed
    # as numbers and right-justified. Otherwise, make a note for .xlsx time to
    # force left-justify on this column!
    collected_table[ARTICLES[0]["title_column"]] = collected_table[ARTICLES[0]["title_column"]].astype(str)

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
