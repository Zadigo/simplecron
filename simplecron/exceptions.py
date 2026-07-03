

class IntervalError(Exception):
    """Raised when an invalid interval is provided for a job."""

    def __init__(self, value: int, expected: str = "greater than 0"):
        super().__init__(
            f"Invalid interval: {value}. Interval must be {expected}.")


class SchedulerNotFoundError(Exception):
    """Raised when a job is created without an associated scheduler."""

    message: str = "No scheduler found for the job."

    def __init__(self):
        super().__init__(self.message)


class ScheduleValueError(Exception):
    """Raised when a job is scheduled with an invalid value."""

    def __init__(self, value: int):
        super().__init__(
            f"start_day can only be used with 'weeks' unit, not '{value}'.")
