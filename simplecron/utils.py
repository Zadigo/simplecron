import datetime

import enum


class TimeUnit(enum.Enum):
    SECONDS = "seconds"
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"
    YEARS = "years"


TIME_UNITS = list(map(lambda unit: unit.value, TimeUnit))


class EventListenerEnum(enum.Enum):
    BEFORE_ALL = "before_all"
    BEFORE = "before"
    AFTER = "after"


EVENT_LISTENERS = list(map(lambda listener: listener.value, EventListenerEnum))


def weekdays(day: str) -> int:
    """Convert a weekday name to its corresponding 
    index (0 for Monday, 6 for Sunday)."""
    weekdays = (
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    )
    if day not in weekdays:
        raise ValueError(
            f"Invalid start day (valid start days are {weekdays})"
        )
    return weekdays.index(day)


def move_to_next_weekday(dt: datetime.datetime, target_weekday: str) -> datetime.datetime:
    """Move the given datetime to the next occurrence of the specified weekday.

    Args:
        dt (datetime.datetime): The original datetime.
        target_weekday (str): The target weekday (e.g., "monday", "tuesday").

    Returns:
        datetime.datetime: The adjusted datetime moved to the next occurrence of the target weekday.
    """
    index = weekdays(target_weekday)
    days_ahead = index - dt.weekday()
    if days_ahead <= 0:  # Target day already passed this week
        days_ahead += 7
    return dt + datetime.timedelta(days=days_ahead)
