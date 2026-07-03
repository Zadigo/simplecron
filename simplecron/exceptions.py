

class IntervalError(Exception):
    def __init__(self, value: int, expected: str = "greater than 0"):
        super().__init__(
            f"Invalid interval: {value}. Interval must be {expected}.")


class SchedulerNotFoundError(Exception):
    message: str = "No scheduler found for the job."

    def __init__(self):
        super().__init__(self.message)


class ScheduleValueError(Exception):
    def __init__(self, value: int):
        items = ['hours', 'days', 'minutes']
        super().__init__(
            f"Invalid schedule value: {value}. Must be one of {', '.join(items)}."
        )


class AtScheduleError(Exception):
    def __init__(self, unit: str):
        super().__init__(
            "Invalid unit for 'at' scheduling. The 'at' method requires the unit to be either 'hours' or 'days'."
        )
