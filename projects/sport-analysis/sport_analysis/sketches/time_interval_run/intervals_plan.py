import click


# TODO
class IntervalsPlan:
    def __init__(self):
        pass

    @staticmethod
    def _parse_string(value: str):
        pass

    @classmethod
    def make_from_string(cls, value: str):
        """
        Factory method to use to instantiate this class,
         like: ActivityId.make_from_string("LATEST-3").
        """
        return cls(
            *cls._parse_string(value),
        )


class BaseIntervalsPlanException(Exception): ...


class ValidationError(BaseIntervalsPlanException): ...


class IntervalsPlanParamType(click.ParamType):
    """
    Parameter type that can be a Garmin or Strava activity as string.
    Eg. garmin-23309590263 | g-23309590263 | strava-18988079605 | s-18988079605
        | LATEST | LATEST-3 | LATEST-RUN | LATEST-RIDE | LATEST-RUN-3.
    """

    name = "intervals_plan"

    def __init__(
        self,
        do_allow_latest_activity_type_run=True,  # To allow LATEST-RUN | LATEST-RUN-3.
        do_allow_latest_activity_type_ride=True,  # To allow LATEST-RIDE | LATEST-RIDE-3.
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.do_allow_latest_activity_type_run = do_allow_latest_activity_type_run
        self.do_allow_latest_activity_type_ride = do_allow_latest_activity_type_ride

    def convert(self, value, param=None, ctx=None) -> IntervalsPlan:

        try:
            return IntervalsPlan.make_from_string(value)
        except (ValidationError, ValueError) as exc:
            self.fail(str(exc), param, ctx)
