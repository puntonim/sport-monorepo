import click
import pytest

from sport_analysis.base_cli_view import (
    ActivityId,
    ActivityIdParamType,
    ValidationError,
)


class TestActivityId:
    def test_no_args(self):
        with pytest.raises(ValueError):
            ActivityId()

    def test_strava_happy_flow(self):
        a = ActivityId(strava_id=18988079605)
        assert a.strava_id == 18988079605
        assert not a.garmin_id
        assert not a.latest_id
        assert not a.latest_activity_type

    def test_strava_id_small_int(self):
        with pytest.raises(ValueError):
            ActivityId(strava_id=1898)
        with pytest.raises(ValueError):
            ActivityId(strava_id=0)
        with pytest.raises(ValueError):
            ActivityId(strava_id=-18988079605)

    def test_strava_id_string(self):
        with pytest.raises(ValueError):
            ActivityId(strava_id="18988079605")

    def test_strava_extra_arg(self):
        for k, v in dict(
            # strava_id=18988079605,
            garmin_id=23309590263,
            latest_id=-1,
        ).items():
            with pytest.raises(ValueError):
                ActivityId(strava_id=18988079605, **{k: v})

    def test_garmin_happy_flow(self):
        a = ActivityId(garmin_id=23309590263)
        assert not a.strava_id
        assert a.garmin_id == 23309590263
        assert not a.latest_id
        assert not a.latest_activity_type

    def test_garmin_id_small_int(self):
        with pytest.raises(ValueError):
            ActivityId(garmin_id=233)
        with pytest.raises(ValueError):
            ActivityId(garmin_id=0)
        with pytest.raises(ValueError):
            ActivityId(garmin_id=-23309590263)

    def test_garmin_id_string(self):
        with pytest.raises(ValueError):
            ActivityId(garmin_id="23309590263")

    def test_garmin_extra_arg(self):
        for k, v in dict(
            strava_id=18988079605,
            # garmin_id=23309590263,
            latest_id=-1,
        ).items():
            with pytest.raises(ValueError):
                ActivityId(garmin_id=18988079605, **{k: v})

    def test_latest_happy_flow(self):
        a = ActivityId(latest_id=-3)
        assert not a.strava_id
        assert not a.garmin_id
        assert a.latest_id == -3
        assert not a.latest_activity_type

    def test_latest_0(self):
        a = ActivityId(latest_id=0)
        assert not a.strava_id
        assert not a.garmin_id
        assert a.latest_id == 0
        assert not a.latest_activity_type

    def test_latest_id_positive(self):
        with pytest.raises(ValueError):
            ActivityId(latest_id=1)
        with pytest.raises(ValueError):
            ActivityId(latest_id=2342342)

    def test_latest_id_string(self):
        with pytest.raises(ValueError):
            ActivityId(latest_id="-1")

    def test_latest_extra_arg(self):
        for k, v in dict(
            strava_id=18988079605,
            garmin_id=23309590263,
            # latest_id=-1,
        ).items():
            with pytest.raises(ValueError):
                ActivityId(latest_id=-3, **{k: v})

    def test_latest_run_happy_flow(self):
        a = ActivityId(latest_id=-3, latest_activity_type="RUN")
        assert not a.strava_id
        assert not a.garmin_id
        assert a.latest_id == -3
        assert a.latest_activity_type == "RUN"

    def test_latest_run_0(self):
        a = ActivityId(latest_id=0, latest_activity_type="RUN")
        assert not a.strava_id
        assert not a.garmin_id
        assert a.latest_id == 0
        assert a.latest_activity_type == "RUN"

    def test_latest_run_id_positive(self):
        with pytest.raises(ValueError):
            ActivityId(latest_id=1, latest_activity_type="RUN")
        with pytest.raises(ValueError):
            ActivityId(latest_id=2342342, latest_activity_type="RUN")

    def test_latest_run_id_string(self):
        with pytest.raises(ValueError):
            ActivityId(latest_id="-1", latest_activity_type="RUN")

    def test_latest_ride_happy_flow(self):
        a = ActivityId(latest_id=-3, latest_activity_type="RIDE")
        assert not a.strava_id
        assert not a.garmin_id
        assert a.latest_id == -3
        assert a.latest_activity_type == "RIDE"

    def test_latest_activity_type_unknown(self):
        with pytest.raises(ValueError):
            ActivityId(latest_id=3, latest_activity_type="XXX")

    def test_latest_activity_type_run_not_allowed(self):
        with pytest.raises(ValueError):
            ActivityId(
                latest_id=-3,
                latest_activity_type="RUN",
                do_allow_latest_activity_type_run=False,
            )
        ActivityId(
            latest_id=-3,
            latest_activity_type="RUN",
            do_allow_latest_activity_type_ride=False,
        )

    def test_latest_activity_type_ride_not_allowed(self):
        with pytest.raises(ValueError):
            ActivityId(
                latest_id=-3,
                latest_activity_type="RIDE",
                do_allow_latest_activity_type_ride=False,
            )
        ActivityId(
            latest_id=-3,
            latest_activity_type="RIDE",
            do_allow_latest_activity_type_run=False,
        )


class TestActivityIdMakeFromString:
    def test_not_string(self):
        with pytest.raises(ValidationError):
            ActivityId.make_from_string(18988079605)

    def test_not_valid_format(self):
        with pytest.raises(ValidationError):
            ActivityId.make_from_string("xxx-18988079605")
        with pytest.raises(ValidationError):
            ActivityId.make_from_string("st-18988079605")
        with pytest.raises(ValidationError):
            ActivityId.make_from_string("stravaXXX-18988079605")
        with pytest.raises(ValidationError):
            ActivityId.make_from_string("s-18988079605X")
        with pytest.raises(ValidationError):
            ActivityId.make_from_string("LATESTXX")
        with pytest.raises(ValidationError):
            ActivityId.make_from_string("LATEST--")
        with pytest.raises(ValidationError):
            ActivityId.make_from_string("LATEST-RUNNN")
        with pytest.raises(ValidationError):
            ActivityId.make_from_string("LATEST RUN")

    def test_strava_happy_flow(self):
        a = ActivityId.make_from_string("strava-18988079605")
        assert a.strava_id == 18988079605
        assert not a.garmin_id
        assert not a.latest_id
        assert not a.latest_activity_type

    def test_strava_s(self):
        a = ActivityId.make_from_string("s-18988079605")
        assert a.strava_id == 18988079605
        assert not a.garmin_id
        assert not a.latest_id
        assert not a.latest_activity_type

    def test_strava_small_int(self):
        with pytest.raises(ValidationError):
            ActivityId.make_from_string("s-1898")

    def test_garmin_happy_flow(self):
        a = ActivityId.make_from_string("garmin-23309590263")
        assert not a.strava_id
        assert a.garmin_id == 23309590263
        assert not a.latest_id
        assert not a.latest_activity_type

    def test_garmin_g(self):
        a = ActivityId.make_from_string("g-23309590263")
        assert not a.strava_id
        assert a.garmin_id == 23309590263
        assert not a.latest_id
        assert not a.latest_activity_type

    def test_garmin_small_int(self):
        with pytest.raises(ValidationError):
            ActivityId.make_from_string("g-1898")

    def test_latest_happy_flow(self):
        a = ActivityId.make_from_string("LATEST-3")
        assert not a.strava_id
        assert not a.garmin_id
        assert a.latest_id == -3
        assert not a.latest_activity_type

    def test_latest_0(self):
        for a in (
            ActivityId.make_from_string("LATEST"),
            ActivityId.make_from_string("LATEST-0"),
        ):
            assert not a.strava_id
            assert not a.garmin_id
            assert a.latest_id == -0
            assert not a.latest_activity_type

    def test_latest_positive(self):
        with pytest.raises(ValidationError):
            ActivityId.make_from_string("LATEST+3")

    def test_latest_run_happy_flow(self):
        a = ActivityId.make_from_string("LATEST-RUN-3")
        assert not a.strava_id
        assert not a.garmin_id
        assert a.latest_id == -3
        assert a.latest_activity_type == "RUN"

    def test_latest_ride_happy_flow(self):
        a = ActivityId.make_from_string("LATEST-RIDE-5")
        assert not a.strava_id
        assert not a.garmin_id
        assert a.latest_id == -5
        assert a.latest_activity_type == "RIDE"

    def test_latest_run_0(self):
        for a in (
            ActivityId.make_from_string("LATEST-RUN"),
            ActivityId.make_from_string("LATEST-RUN-0"),
        ):
            assert not a.strava_id
            assert not a.garmin_id
            assert a.latest_id == 0
            assert a.latest_activity_type == "RUN"

    def test_latest_activity_type_unknown(self):
        with pytest.raises(ValidationError):
            ActivityId.make_from_string("LATEST-XXX-3")


class TestActivityIdParamType:
    # Note: only basic tests as all the tests above are enough.

    def test_happy_flow(self):
        a = ActivityIdParamType().convert("strava-18988079605")
        assert a.strava_id == 18988079605
        assert not a.garmin_id
        assert not a.latest_id
        assert not a.latest_activity_type
        a = ActivityIdParamType().convert("s-18988079605")
        assert a.strava_id == 18988079605
        assert not a.garmin_id
        assert not a.latest_id
        assert not a.latest_activity_type
        a = ActivityIdParamType().convert("LATEST-RUN-3")
        assert not a.strava_id
        assert not a.garmin_id
        assert a.latest_id == -3
        assert a.latest_activity_type == "RUN"

    def test_not_valid_format(self):
        with pytest.raises(click.exceptions.BadParameter):
            ActivityIdParamType().convert("s-189")
        with pytest.raises(click.exceptions.BadParameter):
            ActivityIdParamType().convert("XXX-18988079605")
        with pytest.raises(click.exceptions.BadParameter):
            ActivityIdParamType().convert(18988079605)
        with pytest.raises(click.exceptions.BadParameter):
            ActivityIdParamType().convert("LATEXXX")
        with pytest.raises(click.exceptions.BadParameter):
            ActivityIdParamType().convert("LATEST-XXX")
