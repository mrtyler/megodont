#!/usr/bin/env python


from functools import wraps
import json
import logging
import os
import math
import re
import sys
import time

import aiohttp
import asyncio
import click
import pandas as pd

import defaults


CACHE_DIR_NAME = "_cache"
CACHE_FILE_MAX_AGE_DAYS = 1
FINAL_AUTHOR_COLUMN_NAME = "Author"
FINAL_TITLE_COLUMN_NAME = "Title"


# From https://github.com/pallets/click/issues/2033
def make_sync(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


def get_cache_filename(url):
    """
    >>> get_cache_filename("https://foo.com/bar/baz")
    '_cache/foo.com__bar__baz'
    """
    filename = url.partition("://")[2].replace("/", "__")
    return os.path.join(get_or_make_cache_dir(), filename)


def get_or_make_cache_dir():
    """
    >>> get_or_make_cache_dir()
    '_cache'
    """
    dirname = CACHE_DIR_NAME
    # This gets created under (doc)test as a side-effect :/
    os.makedirs(dirname, exist_ok=True)
    return dirname


def get_age(file):
    if not os.path.exists(file):
        return math.inf
    return (time.time() - os.path.getmtime(file)) / 86400  # days


async def fetch_urls(data_sources, force_refetch=False):
    logging.warning("Fetching data sources...")
    # Use a set to weed out duplicates, both to be nice to remote servers
    # and to prevent collisions while writing cache files async :).
    urls = set([source["url"] for source in data_sources])
    # From https://stackoverflow.com/questions/35196974/aiohttp-set-maximum-number-of-requests-per-second
    # Picking very conservative numbers for now.
    connector = aiohttp.TCPConnector(limit=5, limit_per_host=2)
    async with aiohttp.ClientSession(
        connector=connector, raise_for_status=True
    ) as session:
        for url in urls:
            cache_file = get_cache_filename(url)
            cache_file_age = get_age(cache_file)
            if force_refetch or cache_file_age > CACHE_FILE_MAX_AGE_DAYS:
                logging.info(f"...fetching {url}")
                logging.debug(
                    f"......to {cache_file} (age {cache_file_age}, max age {CACHE_FILE_MAX_AGE_DAYS}, force {force_refetch})"
                )
                async with session.get(url) as response:
                    html = await response.text()
                    with open(cache_file, "w") as ff:
                        ff.write(html)
            else:
                logging.info(f"...skipping {url} because it is cached")
                logging.debug(
                    f"......to {cache_file} (age {cache_file_age}, max age {CACHE_FILE_MAX_AGE_DAYS}, force {force_refetch})"
                )


def read_url(url):
    logging.info(f"Reading {url}...")
    tables = pd.read_html(get_cache_filename(url), flavor="bs4")
    return tables


def find_target_table(tables, source):
    target_table = None
    for table in tables:
        if all([column in table.columns for column in source["target_table_columns"]]):
            target_table = table
            break
    else:
        raise ValueError("Couldn't find target table")
    return target_table


def drop_unwanted_columns(table, source):
    for column in table.columns:
        if column not in source["target_table_columns"]:
            print(f"Dropping column {column}")
            table = table.drop(column, axis=1)
    return table


def resolve_duplicates(collected_table, table):
    # Workaround for "ValueError: You are trying to merge on int64 and object
    # columns. If you wish to proceed you should use pd.concat" from
    # https://stackoverflow.com/questions/64385747/valueerror-you-are-trying-to-merge-on-object-and-int64-columns-when-use-pandas
    for tt in (collected_table, table):
        tt["Year"] = tt["Year"].astype(str)

    join_columns = [FINAL_AUTHOR_COLUMN_NAME, FINAL_TITLE_COLUMN_NAME, "Category"]
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
        "Year_x": 999999,  # Must be > all real years so we can drop it with min() later
        "Significance_x": 0,
        "Awards_x": "",
        "Year_y": 999999,  # Must be > all real years so we can drop it with min() later
        "Significance_y": 0,
        "Awards_y": "",
    }
    new_table = new_table.fillna(value=fill_values)

    # Hugo and Nebula in particular have different rules for award dates for
    # many books (e.g. Paladin of Souls). We'll keep the earliest date that we
    # see.
    for column in ("Year",):
        # Use insert() to keep Year as the first column
        new_table.insert(
            0,
            column,
            new_table[f"{column}_x"]
            .astype(int)
            .combine(new_table[f"{column}_y"].astype(int), min),
        )
        new_table = new_table.drop(f"{column}_x", axis=1)
        new_table = new_table.drop(f"{column}_y", axis=1)
    for column in (
        "Significance",
        "Awards",
    ):
        new_table[column] = new_table[f"{column}_x"] + new_table[f"{column}_y"]
        new_table = new_table.drop(f"{column}_x", axis=1)
        new_table = new_table.drop(f"{column}_y", axis=1)

    return new_table


def merge_or_init_human_columns(collected_table, infile):
    def init_human_columns(collected_table):
        collected_num_rows = collected_table.shape[0]
        # String "0" because of resolve_duplicates() things
        zero_col = ["0" for _ in range(collected_num_rows)]
        collected_table = collected_table.assign(Rating=zero_col)
        empty_col = ["" for _ in range(collected_num_rows)]
        collected_table = collected_table.assign(WhenRead=empty_col)
        collected_table = collected_table.assign(Notes=empty_col)
        return collected_table

    def merge_human_columns(collected_table, infile):
        human_table = pd.read_csv(infile)
        join_columns = [FINAL_AUTHOR_COLUMN_NAME, FINAL_TITLE_COLUMN_NAME]
        collected_table = collected_table.merge(
            human_table, on=join_columns, how="outer"
        )

        if any(
            [
                f"{col}_x" in collected_table.columns
                or f"{col}_y" in collected_table.columns
                for col in join_columns
            ]
        ):
            raise ValueError("Eyyyyyyy column mismatch??")

        # Resolve "conflicts" by taking the right (human-generated csv) side
        # for the human-managed columns...
        human_columns = (
            "Rating",
            "WhenRead",
            "Notes",
        )
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
                    left_of_human_columns_pos = len(collected_table.columns) - len(
                        human_columns
                    )
                    collected_table.insert(
                        left_of_human_columns_pos, column_root, collected_table[column]
                    )
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
    if os.path.exists(infile):
        collected_table = merge_human_columns(collected_table, infile)
    return collected_table


@click.command()
@click.option(
    "--configfile",
    default="configs/default.json",
    show_default=True,
    help="JSON config file describing data sources (e.g. Wikipedia articles) to collect.",
)
@click.option(
    "--force-refetch/--no-force-refetch",
    default=False,
    show_default=True,
    help="Ignore existing cache and re-fetch data sources",
)
@click.option("--infile", default=None, help="File with existing data to merge in")
@click.option(
    "--loglevel",
    default="info",
    show_default=True,
    help="Verbosity of log output ('debug' through 'error')",
)
@click.option(
    "--outfile",
    default=defaults.outfile,
    show_default=True,
    help="Where to write the data at the end",
)
@make_sync
async def main(configfile, force_refetch, infile, loglevel, outfile):
    # CLI validation. This should move elsewhere. Like to a wrapper script that implements the same interface as a web client, maybe.
    if infile and not os.path.exists(infile):
        print(f"You specified --infile {infile} but I can't find it :(. Exiting.")
        # Another reason to move this to a CLI-only area.
        sys.exit(2)
    if infile is None:
        infile = "books - books.csv.csv"

    numeric_loglevel = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_loglevel, int):
        raise ValueError(f"Invalid log level: {loglevel}")
    logging.basicConfig(
        format="%(asctime)s:%(levelname)s:%(message)s", level=loglevel.upper()
    )

    if configfile and not os.path.exists(configfile):
        print(
            f"You specified --configfile {configfile} but I can't find it :(. Exiting."
        )
        # Another reason to move this to a CLI-only area.
        sys.exit(2)
    with open(configfile, "r") as cf:
        data_sources = json.load(cf)

    await fetch_urls(data_sources, force_refetch)

    collected_table = None
    for source in data_sources:
        tables = read_url(source["url"])
        table = find_target_table(tables, source)

        table = drop_unwanted_columns(table, source)

        print("Normalizing author and title column names")
        table = table.rename(
            columns={
                source["author_column"]: FINAL_AUTHOR_COLUMN_NAME,
                source["title_column"]: FINAL_TITLE_COLUMN_NAME,
            }
        )

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
        table = table.replace(
            to_replace=r" \(also known as .*\)$", value=r"", regex=True
        )

        print("Dropping rows when no award given")
        # Drop "Not awarded" and variants
        table = table[table[FINAL_AUTHOR_COLUMN_NAME] != "Not awarded"]
        table = table[table[FINAL_AUTHOR_COLUMN_NAME] != "(no award)+"]

        print("Dropping some repeat entries")
        # The wikipedia article says, "_The Moon Is a Harsh Mistress_ was
        # serialized in 1965–66, and was allowed to be nominated for both
        # years."
        #
        # That's not helpful for our purposes, so we'll drop the 1966 Hugo
        # Novel Nomination and go with the 1967 Hugo Novel Win (which will
        # later merge with the 1967 Nebula Novel Nomination).
        table = table.drop(
            table[
                (table[FINAL_TITLE_COLUMN_NAME] == "The Moon Is a Harsh Mistress")
                & (table["Year"] == "1966")
            ].index
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
        table = table[table[FINAL_TITLE_COLUMN_NAME] != "Dune World"]

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
        # This is the old strategy where all Awards are piled together as text
        awards_col = []
        # This is the new strategy where each Award gets its own column (and these columsn are glued together later)
        award_col = []
        significance_col = []
        for row in table.iterrows():
            if row[1][FINAL_AUTHOR_COLUMN_NAME].endswith("*") or source.get(
                "winners_only"
            ):
                awards_col.append(
                    f"{source['award']} {source['category']} Win({source['winner_score']}), "
                )
                significance_col.append(source["winner_score"])
                award_col.append(source["winner_score"])
            else:
                awards_col.append(
                    f"{source['award']} {source['category']} Nom({source['nominee_score']}), "
                )
                significance_col.append(source["nominee_score"])
                award_col.append(source["nominee_score"])
        award_col_title = f"{source['award']} {source['category']} ({source['winner_score']}/{source['nominee_score']})"
        new_cols = {
            "Awards": awards_col,
            # Only used for joining; will be dropped later
            "Category": [source["category"] for _ in range(table.shape[0])],
            "Significance": significance_col,
            award_col_title: award_col,
        }
        table = table.assign(**new_cols)

        # first middle middle+ last -> last, first middle middle+
        #
        # Weird logic to treat ' (translator)' as part of the last name. Had to
        # add non-'(' to non-space to make it work.
        print("Removing trailing * from author names")
        table = table.replace(
            to_replace={FINAL_AUTHOR_COLUMN_NAME: r"\*$"},
            value={FINAL_AUTHOR_COLUMN_NAME: r""},
            regex=True,
        )
        print("Changing author names to last, first")
        table = table.replace(
            to_replace={FINAL_AUTHOR_COLUMN_NAME: r"(.*) ([^ (]+( \(translator\))?)"},
            value={FINAL_AUTHOR_COLUMN_NAME: r"\2, \1"},
            regex=True,
        )
        # Special case: Ursula K. Le Guin
        table = table.replace(
            to_replace={
                FINAL_AUTHOR_COLUMN_NAME: "Guin, Ursula K. Le",
            },
            value={
                FINAL_AUTHOR_COLUMN_NAME: "Le Guin, Ursula K.",
            },
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

    print("Final cleanup")
    collected_table = collected_table.replace(
        to_replace={"Awards": r", $"}, value={"Awards": r""}, regex=True
    )
    collected_table = collected_table.drop("Category", axis=1)
    collected_table["Significance"] = collected_table["Significance"].astype(int)

    print("Populating human-filled columns")
    collected_table = merge_or_init_human_columns(collected_table, infile)

    # Sort it out
    print("Sorting data")
    collected_table = collected_table.sort_values(
        by=["Year", "WhenRead"],
    )
    collected_table = collected_table.sort_values(
        by=["Significance", "Rating", "Awards"], ascending=False
    )

    # Write it down
    print("Writing csv")
    with open(outfile, "w") as ff:
        ff.write(collected_table.to_csv(index=False))


if __name__ == "__main__":
    main()
