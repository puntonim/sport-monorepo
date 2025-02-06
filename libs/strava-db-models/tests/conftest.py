import pytest
from peewee_utils import peewee_utils

import strava_db_models


@pytest.fixture(autouse=True, scope="function")
def test_settings_fixture(monkeypatch, request):
    # settings.IS_TEST = True
    ...


@pytest.fixture(autouse=True, scope="function")
def create_db_fixture(test_settings_fixture, monkeypatch, request):
    # Note that the signature includes `test_settings_fixture` because we need that
    #  fixture to be executed before this one.

    # Configure peewee_utils with the SQLite DB path.
    peewee_utils.configure(sqlite_db_path=":memory:")

    # Register all tables, triggers and sql_functions.
    strava_db_models.register_default_tables_and_triggers_and_sql_functions()

    # To achieve tests isolation we create a new (in-memory) database (invoking db_init()
    #  a new time) for every test method, and then we create all tables.
    peewee_utils._db_init()
    peewee_utils.create_all_tables()
    yield
    if not peewee_utils.db.is_closed():
        peewee_utils.db.close()
