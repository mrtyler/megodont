# TODO

## Initial release wishlist

The 0.0.1 release runs in a clean environment and makes a .csv from scratch and merges with an existing .csv without clobbering user data. Huzzah!

But a lot of stuff is hardcoded. There are no tests. There is no release process. This was my first time using pandas and I-have-no-idea-what-I'm-doing-dog.jpg.

Here's a collection of things I'm at least thinking about before initial release. This includes a slightly less noisy distillation of what was left in the enormous TODO at the top of `wikipedia_books.py`.

* ~Basic operations, removing hardcoded paths, command-line args~

* Scraping
** (Moving this up in priority because waiting for all the fetches is bad for the feedback loop and it's kinda anti-social anyway)
** Local cache to prevent spurious fetches
** Threads for fetches
** Retries for fetches

* Generate/specify/persist Configs
** To start, at least: default, tyler (copy of default probably)
** This framework feels important for a web or api interface
** Specify Config as JSON blob in file or via api
** Probably more of an MVP of this for a first pass
** Good news: click effectively uses function args as its interface. I was thinking the web interface would do similar: a flask-decorated method to deal with http request and json blob mangling etc. that calls main()

* Resolve the Beggars In Spain problem
** Separate files per category?
** One file but join on category so they stay separate?
** Configurable behavior for this choice?

* Code cleanup
** Organize things into functions more seriously
** Basic unit test scaffolding
** Specifically some kind of acceptance test related to user-generated data!

* CI/CD and Releases
** Github Actions seems simple/easy enough
** Some kind of interface for unittest, acceptancetest, deploy-to-drive, etc. Tox? Make??
** Drive integration deserves its own bullet. Dedicated account (presumably). Versioning/naming?
** Github integration also deserves a bullet. Maybe I need Terraform (with accompanying Github integration plus potentially AWS integration) to IaC config of the Github repo?

* Docs
** Mostly links and how the above implemented stuff works

* Generate .xlsx
** Enables additional features: one sheet per category instead of separate sheets (and/or all the optionality of this); formula to calculate Significance.

* Data improvements
** More categories (novellettes), more awards (retro hugos, British Sci-Fi one, etc.)
** Specific entry cleanup: Press Enter [emoji]; Walter M. Miller, Jr. and james tiptree, jr.; Connie Willis Bellwether/Remake Nebula Novel/Locus Novella overlap
** Combine multiple author entries: co-authors, translators, etc.
