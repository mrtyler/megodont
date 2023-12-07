# TODO

## Initial release wishlist

The 0.0.1 release runs in a clean environment and makes a .csv from scratch and merges with an existing .csv without clobbering user data. Huzzah!

But a lot of stuff is hardcoded. There are no tests. There is no release process. This was my first time using pandas and I-have-no-idea-what-I'm-doing-dog.jpg.

Here's a collection of things I'm at least thinking about before initial release. This includes a slightly less noisy distillation of what was left in the enormous TODO at the top of `wikipedia_books.py`.

* ~Basic operations, removing hardcoded paths, command-line args~

* ~Generate/specify/persist Configs~

* ~Scraping improvements~
** ~Cache pages locally. Add --force-refetch~
** ~Use aiohttp for better performance later. Add conservative throttling~

* Resolve the Beggars In Spain problem
** Separate files per category?
** One file but join on category so they stay separate?
** Configurable behavior for this choice?
** Grab everything and filter at the end or go category by cateory through `config[*]["category"]`?

* CI/CD and Releases
** Github Actions seems simple/easy enough
** Some kind of interface for unittest, acceptancetest, deploy-to-drive, etc. Tox? Make??
** Drive integration deserves its own bullet. Dedicated account (presumably). Versioning/naming?
** Github integration also deserves a bullet. Maybe I need Terraform (with accompanying Github integration plus potentially AWS integration) to IaC config of the Github repo?

* Code cleanup
** Organize things into functions more seriously
** Basic unit test scaffolding
** Specifically some kind of acceptance test related to user-generated data!
** SOON move make_sync to this level and do hopefully "true" async here (and make main() decorator situation less confusing)
** SOON need to establish cli.py
** LATER Retries for fetches, maybe backoff
*** ```
if response.status not in (200, 429,):
     raise aiohttp.ClientResponseError()
```
** LATER support file:/// (maybe specially as i guess aiohttp isn't smart enough? or maybe i need that third / and an absolute path?) or some other way to specify non-http data sources
** LATER setuptools or whatever wrapper can be the undecorated megodont entry point.
** LATER remove my real ratings and such for better/smaller surface area'd canned data?

* Docs
** Mostly links and how the above implemented stuff works

* Data improvements
** Combine multiple author entries: co-authors, translators, etc.
** More categories (novellettes), more awards (retro hugos, British Sci-Fi one, etc.)
** Specific entry cleanup: Press Enter [emoji]; Walter M. Miller, Jr. and james tiptree, jr.; Connie Willis Bellwether/Remake Nebula Novel/Locus Novella overlap

* Generate .xlsx
** Enables additional features: one sheet per category instead of separate sheets (and/or all the optionality of this); formula to calculate Significance.
** Title "2312" gets right-justified because it's a number. astype(str) doesn't help, so looks like this needs to be fixed with left-justify specifically
