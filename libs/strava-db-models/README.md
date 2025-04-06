**Sport monorepo: Strava DB Models**
====================================

Just [Peewee ORM](https://github.com/coleifer/peewee) data models for Strava objects.


Usage
=====

---

See top docstrings in [strava_db_models.py](strava_db_models/strava_db_models.py).

Used, at the moment, by:
 - strava-exporter-to-db in sport-monorepo


Local dir install
-----------------
To install these models in a project, from a local dir, add this to `pyproject.toml`:
```toml
[project]
...
dependencies = [
    "strava-db-models @ ../libs/strava-db-models"
    # "strava-db-models @ file:///Users/myuser/workspace/sport-monorepo/libs/strava-db-models"
]

[tool.poetry.dependencies]
# This section is required only when there are editable (develop = true) dependencies.
strava-db-models = {develop = true}
```

Github install
--------------
To install this client in a project, from Github, add this to `pyproject.toml`:
```toml
[project]
...
dependencies = [
    "strava-db-models @ git+https://github.com/puntonim/sport-monorepo#subdirectory=libs/strava-db-models",
]
```

Pip install
-----------
```sh
$ pip install "strava-db-models @ git+https://github.com/puntonim/sport-monorepo#subdirectory=libs/strava-db-models"
```


Development setup
=================

---

See [README.md](../README.md) in the lib subdir.


Copyright
=========

---

Copyright puntonim (https://github.com/puntonim). No License.
