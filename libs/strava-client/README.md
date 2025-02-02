**Strava monorepo: Strava Client**
==================================

Just a Python client for Strava API.\
It supports 2 types of auth:
 - Strava token stored to a local file;
 - Strava token, client id and client secret stored in AWS Parameter Store.

To use AWS Parameter Store, then install the extra `aws-parameter-store`.

Note: see project `strava-facade-api` to know how to get Strava API keys (token).

API v3 docs:
 - https://developers.strava.com/docs/reference/
 - Rate limits - 100 requests every 15 minutes, 1'000 per day, reset at natural
    15-minute intervals corresponding to 0, 15, 30 and 45 minutes after the hour:
    https://developers.strava.com/docs/rate-limits/
 - Webhooks: https://developers.strava.com/docs/webhooks/


Usage
=====

---

See top docstrings in [strava_client.py](strava_client/strava_client.py).

Local dir install
-----------------
To install this client in a project, from a local dir, add this to `pyproject.toml`:
```toml
[project]
...
dependencies = [
    "strava-client @ ../libs/strava-client"
    # "strava-client @ file:///Users/myuser/workspace/strava-monorepo/libs/strava-client"
    # Or, to install the extra AWS Parameter Store:
    # "strava-client[aws-parameter-store] @ file:///Users/myuser/workspace/strava-monorepo/libs/strava-client"
]

[tool.poetry.dependencies]
# This section is required only when there are editable (develop = true) dependencies.
strava-client = {develop = true}
```

Github install
--------------
To install this client in a project, from Github, add this to `pyproject.toml`:
```toml
[project]
...
dependencies = [
    "strava-client @ git+https://github.com/puntonim/strava-monorepo#subdirectory=libs/strava-client",
    # Or, to install the extra AWS Parameter Store:
    # "strava-client[aws-parameter-store] @ git+https://github.com/puntonim/strava-monorepo#subdirectory=libs/strava-client",
]
```

Pip install
-----------
```sh
$ pip install "strava-client @ git+https://github.com/puntonim/strava-monorepo#subdirectory=libs/strava-client"
# Or, to install the extra AWS Parameter Store:
$ pip install "strava-client[aws-parameter-store] @ git+https://github.com/puntonim/strava-monorepo#subdirectory=libs/strava-client",
```


Development setup
=================

---

See [README.md](../README.md) in the lib subdir.


Copyright
=========

---

Copyright puntonim (https://github.com/puntonim). No License.
