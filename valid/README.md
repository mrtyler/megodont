# End-to-end validation

This directory contains:

* *Megodont.scratch.csv* - Latest validated output (2023-12-06) from scratch, i.e. with no `--infile`.
* *Megodont.scratch - Megodont.scratch.csv.csv* - Above `Megodont.csv` after uploading to and downloading from Google Drive.
* *Megodont.infile.csv* - Latest validated output (2023-12-06) using user-generated data, i.e. with `--infile`.
* *Megodont.infile - Megodont.infile.csv.csv* - Above `Megodont.csv` after uploading to and downloading from Google Drive.

## Why the round trip to Google Drive?
This simulates the common operation of taking a Megodont spreadsheet, working with it for a while, then re-running Megodont with this spreadsheet as an `--infile` to update data from data sources while retaining the user-generated data.

Today the only difference is that Drive truncates values like `2023.0` to `2023`. I can fix this at generation time with `astype(int)` for cases like Year. However, this problem will always exist unless we want to truncate everyone's e.g. Ratings column. So I'm not bothering to do this for Year either. (Just noticed that Year only becomes a float as a result of merge operations. Everything else is still true.)

The two files should be identical after:
```
$ sed -e 's/\.0//g' valid/Megodont.scratch.csv > valid/tmp.csv
$ vimdiff valid/Megodont.scratch\ -\ Megodont.scratch.csv.csv valid/tmp.csv
$ rm -f valid/tmp.csv
```
