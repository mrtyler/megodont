# Megodont Development and Other Technical Topics

## Design Principles

### Never lose user-generated data


## CI/CD, Releases, etc.

[[Github Actions]]

### Google Drive integration

* Simplest instructions I could find for creating a Service Account and using it with drive: https://www.labnol.org/google-api-service-account-220404
** Uh did these turn out to be right??

I think it went something like:
* Do the first few steps from above article: have a Google account, enable Drive API, make a Service Account `megodont-uploader`, download json credentials.
* TODO Set `MEGODONT_UPLOADER_CREDS` to the base64-encoded contents of the credentials file.
   * `export MEGODONT_UPLOADER_CREDS=$(base64 < megodont-uploader-credentials.json.base64)`
* Manually create a Drive folder called Megodont. Add Service Account's email as Editor. Note folder ID from its Share URL.
* Add credentials to Github Actions env vars (or locally for testing)

## Development

### Running tests

```
$ tox  # Default is lint + test
$ tox run -e test  # Just the unit tests
$ tox run -e e2e  # Run end-to-end tests
```
