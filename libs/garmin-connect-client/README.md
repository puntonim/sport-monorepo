**Sport monorepo: Garmin Connect Client**
=========================================

Just a Python client for Garmin Connect API.\
Note: this API is not the official one, as that one is not for private customer.
This API is unofficial software that leverages the backend-for-frontend used by 
 Garmin Connect official website.

The main library used is:
 - https://github.com/cyberjunky/python-garminconnect
which under the hood uses this other lib for auth:
- https://github.com/matin/garth

The authentication is interactive and it asks for the username and password used
 in Garmin Connect official website. It gets a token and stores it in a local file
 for months.

Usage
=====

---

See top docstrings in [garmin_connect_client.py](garmin_connect_client/garmin_connect_client.py).


Local dir install
-----------------
To install this client in a project, from a local dir, add this to `pyproject.toml`:
```toml
[project]
...
dependencies = [
    "garmin-connect-client @ ../libs/garmin-connect-client"
    # "garmin-connect-client @ file:///Users/myuser/workspace/sport-monorepo/libs/garmin-connect-client"
]

[tool.poetry.dependencies]
# This section is required only when there are editable (develop = true) dependencies.
garmin-connect-client = {develop = true}
```

Github install
--------------
To install this client in a project, from Github, add this to `pyproject.toml`:
```toml
[project]
...
dependencies = [
    "garmin-connect-client @ git+https://github.com/puntonim/sport-monorepo#subdirectory=libs/garmin-connect-client",
]
```

Pip install
-----------
```sh
$ pip install "garmin-connect-client @ git+https://github.com/puntonim/sport-monorepo#subdirectory=libs/garmin-connect-client"
```


Development setup
=================

---

See [README.md](../README.md) in the lib subdir.


Copyright
=========

---

Copyright puntonim (https://github.com/puntonim). No License.
