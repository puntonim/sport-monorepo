class BaseDomainException(Exception):
    pass


class ActivityNotFoundInStravaApi(BaseDomainException):
    def __init__(self, activity_id: int) -> None:
        self.activity_id = activity_id


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


class RequestedResultsPageDoesNotExistInStravaApi(BaseDomainException):
    def __init__(self, page_n: int):
        self.page_n = page_n


class NaiveDatetimeInput(BaseDomainException):
    def __init__(self, value):
        self.value = value


class PossibleDuplicatedActivityFound(BaseDomainException):
    def __init__(self, activity_id: str | None = None):
        self.activity_id = activity_id


class StravaApiRateLimitExceededError(BaseDomainException):
    pass


class AfterTsInTheFutureInStravaApi(BaseDomainException):
    def __init__(self, after_ts: int):
        self.after_ts = after_ts
