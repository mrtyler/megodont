# Megodont Development and Other Technical Topics

## Design Principles

### Never lose user-generated data


## CI/CD, Releases, etc.

[[Github Actions]]

### Google Drive integration

* Simplest instructions I could find for creating a Service Account and using it with drive: https://www.labnol.org/google-api-service-account-220404


## Development

### Running tests

```
$ tox  # Default is lint + test
$ tox run -e test  # Just the unit tests
$ tox run -e e2e  # Run end-to-end tests
```
