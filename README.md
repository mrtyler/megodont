# Megodont

Megodont collects a dataset from multiple locations, de-dupes and filters the data, and creates a spreadsheet of the data including a Significance Score based on where and how often members were mentioned.

I wrote it to make a spreadsheet of novels (and shorter works) that won or were nominated for the Hugo, Nebula, Locus, and other well-known awards.

My spreadsheet is [[here]].


## About Significance Score

Hugo and Nebula are most significant awards IMO. A win is more impressive than two nominations. Other awards are helpful to break ties, and enough of them can change rankings.

### Tweaking Significance Score

1. Fix the numbers in the spreadsheet, replace Significance column with `=sum(d1:g1)` or whatever.
1. Modify the code and run it locally
1. (Wishlist) Modify values in Configs and run it locally
1. (Wishlist) Generate your own spreadsheet from the web [[link]]


## Running

I use [pyenv](https://github.com/pyenv/pyenv) and `virtualenv`; my workflow is below.

If you're in a hurry, you can raw-dog it and go straight to the `pip install` step and install libraries directly to your system Python.

`virtualenvs` are dope, tho. There are plenty of walkthroughs out there; [here is a quick one](https://click.palletsprojects.com/en/5.x/quickstart/#virtualenv).

```
pyenv virtualenv megodont
pyenv activate megodont
pip install -r requirements.txt
./megodont.py
vi Megodont.csv  # Generated with the default config
```

### Updating the base spreadsheet while retaining user-generated data (Ratings, Notes, etc.)

Megodont will attempt to merge user-generated data from an existing spreadsheet.

```
./megodont.py --infile Megodont-with-my-ratings-and-notes.csv
```

Any rows with user-generated data that can't be merged with the (possibly updated) base spreadsheet are appended to the end. A [design principle](DEVELOPMENT.md) of Megodont is that it must not discard user-generated data!


## Development


## FAQ

* Is there an empty spreadsheet or template?

[[Here]].

* What is a megodont?

"Megodonts groan against spindle cranks, their enormous heads hanging low, prehensile trunks scraping the ground as they tread slow circles around power spindles. The genehacked animals comprise the living heart of the factory’s drive system, providing energy for conveyor lines and venting fans and manufacturing machinery."
--Paolo Bacigalupi, _The Windup Girl_, 2009 Hugo and Nebula Best Novel winner


## History

This project came over from internal repo `2022-aoc`, which started as a place to hold my 2022 Advent of Code exercises and evolved to host a few random things.

This included a script `wikipedia_books.py` where I learned that [[pandas]] can extract CSVs from HTML tables and do a bunch of other data manipulation stuff. This script helped me scratch an itch:

In 2021, I rekindled my interest in sci-fi. I felt under-exposed to The Canon, starting with the fact that I'd never read Ursula Le Guin. My library had _The Lathe of Heaven_ sitting in the Ls, and I was off and running.

Around 2022, I wanted to re-focus my explosively-grown To Be Read list a bit. I don't always agree with critics or awards voters, but under honest circumstances they usually provide at least some signal. Wikipedia helpfully provides the [[list of joint winners]]. The (currently) twenty-six novels there comprise the first phase of my quest.

But what of the next tier down? Surely, after the books that won both awards, the next most Significant books are those that won one award while being nominated for the other. And what if, to break the tie amongst all those works, we could use a less-famous award?

### Archaeology

I extracted these commits from `2022-aoc` using [[https://stackoverflow.com/questions/1365541/how-to-move-some-files-from-one-git-repo-to-another-not-a-clone-preserving-hi]]. Specifially the one liner: `git log --pretty=email --patch-with-stat --reverse --full-index --binary -m --first-parent -- path/to/file_or_folder | (cd /path/to/new_repository && git am --committer-date-is-author-date)`. This version is tagged as `0.0.0`.

### License

I chose 3-clause BSD because this project relies heavily on pandas and pandas uses 3-clause BSD.
