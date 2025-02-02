**Strava monorepo: Libraries**
==============================

Just a collection of standalone Strava Python libraries that can be installed
 individually.\
Projects in this strava-monorepo typically include some of them as local requirements.
Other projects can install them from the Git subdir.


Target Python version
=====================

---

The target is a Python version that is recent enough, but not too recent for a wide
 compatibility.\
Python 3.10 seems a good compromise.\
Note: Python 3.10 introduced the annotation `| None` for optional types, among other things.


Development setup
=================

---

1 - System requirements
----------------------

**Python 3.10**\
The target Python 3.10 for a wide compatibility.\
Install it with pyenv:
```sh
$ pyenv install -l  # List all available versions.
$ pyenv install 3.10.16
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
$ pyenv local 3.10  # It creates `.python-version`, to be git-ignored.
$ pyenv which python
/Users/nimiq/.pyenv/versions/3.10.16/bin/python

# Now create a venv with poetry:
$ poetry env use ~/.pyenv/versions/3.10.16/bin/python
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

These libs are not deployed to PyPI.\
See the individual `README.md` file in each lib subdir to know how to install and use
 each lib.


Copyright
=========

---

Copyright puntonim (https://github.com/puntonim). No License.
