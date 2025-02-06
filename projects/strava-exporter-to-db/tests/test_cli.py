import argparse
from unittest import mock

import pytest

from strava_exporter_to_db.cli import main


class TestCli:
    def test_happy_flow(self):
        with mock.patch("strava_exporter_to_db.cli.ExporterToDb"):
            main(
                [
                    "summaries",
                    "--strategy",
                    "OVERWRITE_IF_CHANGED",
                    "--before-ts",
                    "2025-01-18T14:30:00+01:00",
                    "--after-ts",
                    "2025-01-01T14:30:00+01:00",
                ]
            )

    def test_strategy_is_mandatory(self):
        with mock.patch("strava_exporter_to_db.cli.ExporterToDb"):
            with pytest.raises(Exception):
                main(["summaries"])
            with pytest.raises(argparse.ArgumentError):
                main(["details"])

    def test_ts_are_optional(self):
        with mock.patch("strava_exporter_to_db.cli.ExporterToDb"):
            main(
                [
                    "summaries",
                    "--strategy",
                    "OVERWRITE_IF_CHANGED",
                ]
            )
            main(
                [
                    "details",
                    "--strategy",
                    "ONLY_MISSING",
                ]
            )
