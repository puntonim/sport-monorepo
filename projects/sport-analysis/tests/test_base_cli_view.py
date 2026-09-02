import click
import pytest

from sport_analysis.base_cli_view import (
    ACTIVITY_ID_PARAM_TYPE,
    ActivityId,
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

    def test_latest_0(self):
        a = ActivityId(latest_id=0)
        assert not a.strava_id
        assert not a.garmin_id
        assert a.latest_id == 0

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

    def test_strava_happy_flow(self):
        a = ActivityId.make_from_string("strava-18988079605")
        assert a.strava_id == 18988079605
        assert not a.garmin_id
        assert not a.latest_id

    def test_strava_s(self):
        a = ActivityId.make_from_string("s-18988079605")
        assert a.strava_id == 18988079605
        assert not a.garmin_id
        assert not a.latest_id

    def test_strava_small_int(self):
        with pytest.raises(ValidationError):
            ActivityId.make_from_string("s-1898")

    def test_garmin_happy_flow(self):
        a = ActivityId.make_from_string("garmin-23309590263")
        assert not a.strava_id
        assert a.garmin_id == 23309590263
        assert not a.latest_id

    def test_garmin_g(self):
        a = ActivityId.make_from_string("g-23309590263")
        assert not a.strava_id
        assert a.garmin_id == 23309590263
        assert not a.latest_id

    def test_garmin_small_int(self):
        with pytest.raises(ValidationError):
            ActivityId.make_from_string("g-1898")

    def test_latest_happy_flow(self):
        a = ActivityId.make_from_string("LATEST-3")
        assert not a.strava_id
        assert not a.garmin_id
        assert a.latest_id == -3

    def test_latest_0(self):
        a = ActivityId.make_from_string("LATEST-0")
        assert not a.strava_id
        assert not a.garmin_id
        assert a.latest_id == -0

    def test_latest_positive(self):
        with pytest.raises(ValidationError):
            ActivityId.make_from_string("LATEST+3")


class TestActivityIdParamType:
    # Note: only basic tests as all the tests above are enough.

    def test_happy_flow(self):
        a = ACTIVITY_ID_PARAM_TYPE.convert("strava-18988079605")
        assert a.strava_id == 18988079605
        assert not a.garmin_id
        assert not a.latest_id
        a = ACTIVITY_ID_PARAM_TYPE.convert("s-18988079605")
        assert a.strava_id == 18988079605
        assert not a.garmin_id
        assert not a.latest_id

    def test_not_valid_format(self):
        with pytest.raises(click.exceptions.BadParameter):
            ACTIVITY_ID_PARAM_TYPE.convert("s-189")
        with pytest.raises(click.exceptions.BadParameter):
            ACTIVITY_ID_PARAM_TYPE.convert("XXX-18988079605")
        with pytest.raises(click.exceptions.BadParameter):
            ACTIVITY_ID_PARAM_TYPE.convert(18988079605)
