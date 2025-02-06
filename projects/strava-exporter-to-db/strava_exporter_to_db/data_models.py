from pathlib import Path

import peewee_utils
import strava_db_models

# Import all models, so they can be imported anywhere in this project with:
#  `from .data_models import Activity`
from strava_db_models import Activity, RawActivityDetails, RawActivitySummary

CURR_DIR = Path(__file__).parent
ROOT_DIR = CURR_DIR.parent
SQLITE_DB_PATH = ROOT_DIR / "db.sqlite3"


# Configure peewee_utils with the SQLite DB path.
peewee_utils.configure(sqlite_db_path=str(SQLITE_DB_PATH))

# Register all default tables, triggers and sql_functions.
strava_db_models.register_default_tables_and_triggers_and_sql_functions()
