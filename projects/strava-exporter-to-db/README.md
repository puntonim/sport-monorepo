**Strava monorepo: Strava Exporter to DB**
==========================================

A CLI to export Strava activities to a SQLite DB.


Usage
=====

---

Create and then activate the virtual environment with poetry:
```sh
$ make poetry-create-env 
$ eval $(poetry env activate)
```
Now you can run the command (which is a Poetry script): `export-to-db`.

TLDR
----
To update an existing DB (or create a new DB if it doesn't exist):
```shell
$ make poetry-destroy-and-recreate-env
$ eval $(poetry env activate)
$ export-to-db summaries --strategy OVERWRITE_IF_CHANGED
$ export-to-db details --strategy ONLY_MISSING
```
This will get all summaries from Strava API (which is a chep operation) and write
 to the DB only the summaries that have changed (it computes a checksum).
Then it will get only the new missing details from Strava API (which is an expensive 
 operation that might hit Strava API limits).


Export activity SUMMARIES
-------------------------
Mind that:
    - most relevant data is in the *summary* (only the description is in the *details*);
    - this command will NOT hit Strava API rate limits;
    - strategy OVERWRITE_IF_CHANGED: overwrites summaries already existing in the DB,
       but only if a summary found in Strava API was updated (it compares the content
       checksum with the one in DB).
    - strategy ONLY_MISSING: not supported for summaries.

`$ export-to-db summaries --strategy OVERWRITE_IF_CHANGED --after-ts 2025-01-18T14:30:00+01:00`

Omit the --after-ts option to start from the oldest found in Strava API.
There is also a --before-ts option.

Export activity DETAILS
-----------------------
Mind that:
    - the only relevant data in *details* is the description;
    - this command might hit Strava API rate limits: if so, then a message will tell
       you how to run it again after 15 mins.
    - strategy ONLY_MISSING: it queries the DB for activities with missing details
       and then hit Strava API - this strategy is less likely to hit Strava API
       rate limits;
    - strategy OVERWRITE_IF_CHANGED: overwrites details already existing in the DB,
       but only if details found in Strava API were changed (it compares the content
       checksum with the one in DB) - this strategy is more likely to hit Strava API
       rate limits;

To get all the missing details:
`$ export-to-db details --strategy ONLY_MISSING --after-ts 2025-01-18T14:30:00+01:00`

To get all details, including the ones already in the DB:
`$ export-to-db details --strategy OVERWRITE_IF_CHANGED --after-ts 2025-01-18T14:30:00+01:00`

Omit the --after-ts option to start from the oldest found in Strava API.
There is also a --before-ts option.


Development setup
=================

---

1 - System requirements
----------------------

**Python 3.13**\
The target Python 3.13 as it is the latest available environment at AWS Lambda.\
Install it with pyenv:
```sh
$ pyenv install -l  # List all available versions.
$ pyenv install 3.13.1
```

**Poetry**\
Pipenv is used to manage requirements (and virtual environments).\
Read more about Poetry [here](https://python-poetry.org/). \
Follow the [install instructions](https://python-poetry.org/docs/#osx--linux--bashonwindows-install-instructions).

**Pre-commit**\
Pre-commit is used to format the code with black before each git commit:
```sh
$ pip install --user pre-commit
# On macOS you can also:
$ brew install pre-commit
```

2 - Virtual environment and requirements
----------------------------------------

Create a virtual environment and install all deps with one Make command:
```sh
$ make poetry-create-env
# Or to recreate:
$ make poetry-destroy-and-recreate-env
# Then you can activate the virtual env with:
$ eval $(poetry env activate)
# And later deactivate the virtual env with:
$ deactivate
```

Without using Makefile the full process is:
```sh
# Activate the Python version for the current project:
$ pyenv local 3.13.1  # It creates `.python-version`, to be git-ignored.
$ pyenv which python
~/.pyenv/versions/3.13.1/bin/python

# Now create a venv with poetry:
$ poetry env use ~/.pyenv/versions/3.13.1/bin/python
# Now you can open a shell and/or install:
$ eval $(poetry env activate)
# And finally, install all requirements:
$ poetry install
# And later deactivate the virtual env with:
$ deactivate
```

To add a new requirement:
```sh
$ poetry add requests
$ poetry add pytest --dev  # Dev only.
$ poetry add requests[security,socks]  # With extras.
$ poetry add git+https://github.com/puntonim/strava-monorepo#subdirectory=libs/strava-client  # From git.
$ poetry add "git+https://github.com/puntonim/strava-monorepo#subdirectory=libs/strava-client[aws-parameter-store]"  # From git with extras.
```

3 - Pre-commit
--------------

```sh
$ pre-commit install
```


Deployment
==========

---

This project is a CLI and it is not deployed.


Copyright
=========

---

Copyright puntonim (https://github.com/puntonim). No License.
