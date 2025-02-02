class BaseDomainException(Exception):
    pass


class NoActivityFound(BaseDomainException):
    pass


class ActivityAlreadyHasDescription(BaseDomainException):
    def __init__(self, activity_id: int, description: str) -> None:
        self.activity_id = activity_id
        self.description = description


class StravaAuthenticationError(BaseDomainException):
    pass


class StravaApiError(BaseDomainException):
    pass


class InvalidDatetimeInput(BaseDomainException):
    def __init__(self, value):
        self.value = value


class NaiveDatetimeInput(BaseDomainException):
    def __init__(self, value):
        self.value = value


class PossibleDuplicatedActivityFound(BaseDomainException):
    def __init__(self, activity_id: str | None = None):
        self.activity_id = activity_id
