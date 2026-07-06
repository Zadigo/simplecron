from abc import ABC, abstractmethod
import datetime

import pytz
from simplecron import utils
from typing import Callable, Optional, Self
from enum import Enum


class TimeUnit(Enum):
    SECONDS = "seconds"
    MINUTES = "minutes"
    HOURS = "hours"
    WEEKS = "weeks"
    DAYS = "days"
    MONTHS = "months"


type TypeTimezone = datetime.timezone | pytz.BaseTzInfo


class TBaseSchedule(ABC):
    def __init__(self, tjob: "TJob", unit: TimeUnit, interval: int, timezone: Optional[TypeTimezone] = None):
        self.tjob: "TJob" = tjob
        self.unit: TimeUnit = unit
        self.interval: int = interval
        self.timezone: Optional[TypeTimezone] = timezone or datetime.timezone.utc
        self.at_time: Optional[datetime.time] = None

        if interval > 1 and (unit == TimeUnit.MONTHS or unit == TimeUnit.WEEKS):
            raise ValueError("Single schedules must have an interval of 1.")

    @abstractmethod
    def schedule_next_run(self):
        pass

    @abstractmethod
    def do(self, job_func: Callable[[], None]) -> "TJob":
        pass

    def _move_to_at_time(self, dt: datetime.datetime) -> datetime.datetime:
        """Move the given datetime to the specified 'at' time."""
        if self.at_time is None:
            return dt

        params = {
            'seconds': self.at_time.second,
            'microsecond': 0
        }

        if self.unit == TimeUnit.DAYS or self.start_day:
            params['hour'] = self.at_time.hour

        if self.unit in [TimeUnit.DAYS, TimeUnit.WEEKS] or self.start_day is not None:
            params['minute'] = self.at_time.minute

        new_dt = dt.replace(**params)
        return new_dt


class TBaseScheduleMixin[T = TBaseSchedule]:
    def do(self: T, job_func: Callable[[], None]) -> "TJob":
        return self.tjob


class TMonthly(TBaseSchedule):
    def __init__(self, job: "TJob", unit: TimeUnit, *args, **kwargs):
        super().__init__(job, unit, *args, **kwargs)
        self.start_month: str = None

    def do(self, job_func: Callable[[], None]) -> "TJob":
        self.schedule_next_run()
        return self.tjob

    def schedule_next_run(self):
        current_time = datetime.datetime.now(self.timezone)

        if self.start_month is not None:
            pass

        _next_run = current_time
        period = datetime.timedelta(**{self.unit.value: self.interval})

        _next_run += period
        self.job.next_run = _next_run


class TDaily(TBaseSchedule):
    def __init__(self, job: "TJob", unit: TimeUnit, *args, **kwargs):
        super().__init__(job, unit, *args, **kwargs)
        self.start_day: str = None
        self.unit: TimeUnit = unit

    def do(self, job_func: Callable[[], None]) -> "TJob":
        self.schedule_next_run()
        return self.tjob

    def at(self, using: H, timezone: Optional[datetime.timezone | pytz.BaseTzInfo] = None) -> Self:
        if timezone is None:
            self.timezone = timezone

        using.unit = self.unit
        using.resolve(timezone=self.timezone)
        self.at_time = using.at_time
        return self

    def schedule_next_run(self):
        current_time = datetime.datetime.now(self.timezone)

        _next_run = current_time
        if self.start_day is not None:
            if self.unit != TimeUnit.WEEKS:
                pass

            _next_run = utils.move_to_next_weekday(
                current_time,
                self.start_day
            )

        if self.at_time is not None:
            pass

        # Delta calculation based on the unit
        period = datetime.timedelta(**{self.unit.value: self.interval})
        _next_run += period

        while _next_run <= current_time:
            _next_run += period

        self.tjob.next_run = _next_run


class TScheduler:
    def _run_job(self, job: TJob):
        job.run()

    def create_every(self, interval: int):
        return TJob(interval, scheduler=self)

    # def run_pending(self):
    #     for job in _jobs:
    #         self._run_job(job)


class TJob:
    def __init__(self, interval: int = 1, scheduler: Optional[TScheduler] = None):
        self.interval = interval
        self.at_timezone: Optional[TypeTimezone] = None
        self.next_run: Optional[datetime.datetime] = None
        self.scheduler: Optional[TScheduler] = scheduler
        self.schedule: Optional[TBaseSchedule] = None

    @property
    def month(self) -> TMonthly:
        return TMonthly(self, self.interval, timezone=self.at_timezone)

    @property
    def months(self) -> TMonthly:
        return TMonthly(self, self.interval, timezone=self.at_timezone)

    @property
    def january(self) -> TMonthly:
        instance = TMonthly(
            self,
            TimeUnit.MONTHS,
            self.interval,
            timezone=self.at_timezone
        )
        instance.start_month = "january"
        return instance

    @property
    def day(self) -> TDaily:
        """Starts weekly schedule that runs on the day the job was created. If you want to start on a specific day, use the `at` method."""
        return TDaily(self, TimeUnit.WEEKS, self.interval, timezone=self.at_timezone)

    @property
    def days(self) -> TDaily:
        """Starts a daily schedule that runs every day of the week. If you want to start on a specific day, use the `at` method."""
        return TDaily(self, TimeUnit.DAYS, self.interval, timezone=self.at_timezone)

    @property
    def monday(self) -> TDaily:
        instance = TDaily(
            self,
            TimeUnit.WEEKS,
            self.interval,
            timezone=self.at_timezone
        )
        instance.start_day = "monday"
        return instance

    def run(self):
        if self.schedule is not None:
            self.schedule.schedule_next_run()


class H:
    """Help class to specify the time of day for a job to run.

    To run a job everyday at 01:30:00::

        h = H(hour=1, minute=30)
        default_scheduler.every(1).day.at(h).do(...)

    To run a job every hour when the minute is 15 e.g. 10:15, 11:15, 12:15::

        h = H(minute=15)
        default_scheduler.every(1).hour.at(h).do(...)

    To run a job every minute when the second is 30 e.g. 10:15:30, 10:16:30, 10:17:30::

        h = H(second=30)
        default_scheduler.every(1).minute.at(h).do(...)
    """

    def __init__(self, hour: int = 0, minute: int = 0, second: int = 0):
        if hour is not None and (hour < 0 or hour > 23):
            raise ValueError("Hour must be between 0 and 23.")

        if minute is not None and (minute < 0 or minute > 59):
            raise ValueError("Minute must be between 0 and 59.")

        if second is not None and (second < 0 or second > 59):
            raise ValueError("Second must be between 0 and 59.")

        self.hour = hour
        self.minute = minute
        self.second = second or 0
        self.unit: TimeUnit = None
        self.timezone: Optional[TypeTimezone] = None
        self.at_time: Optional[datetime.time] = None

    def __repr__(self):
        match self.unit:
            case TimeUnit.MINUTES:
                return "H(<Every minute past {second:02d} seconds>)".format(
                    second=self.second,
                )
            case TimeUnit.HOURS:
                return "H(<Every hour past {minute:02d} minutes>)".format(
                    minute=self.minute,
                )
            case TimeUnit.DAYS | TimeUnit.WEEKS:
                return "H(<Every day at {hour:02d}:{minute:02d}:{second:02d}>)".format(
                    hour=self.hour,
                    minute=self.minute,
                    second=self.second
                )
            case _:
                return "H(<Every {unit} at {hour:02d}:{minute:02d}:{second:02d}>)".format(
                    unit=self.unit.value if self.unit else "unknown",
                    hour=self.hour,
                    minute=self.minute,
                    second=self.second
                )

    def resolve(self, timezone: Optional[TypeTimezone] = None):
        if self.unit is None:
            raise ValueError("Time unit is not set.")

        self.timezone = timezone or datetime.timezone.utc

        params = {
            'second': self.second,
            'microsecond': 0
        }

        # Every minute when the second is X.
        # E.g. 10:15:30, 10:16:30, 10:17:30
        if self.unit == TimeUnit.MINUTES:
            params['hour'] = 0
            params['minute'] = 0
            params['second'] = self.second

        # Every hour when the minute is X.
        # E.g. 10:15:00, 11:15:00, 12:15:00
        if self.unit == TimeUnit.HOURS:
            params['hour'] = 0
            params['minute'] = self.minute

        # Every day when the hour is X and the minute is Y.
        # E.g. Monday at 10:15:00, Tuesday at 10:15:00, Wednesday at 10:15:00
        if self.unit in [TimeUnit.DAYS, TimeUnit.WEEKS]:
            params['hour'] = self.hour
            params['minute'] = self.minute
            params['second'] = self.second

        # Every <unit> when the hour is X, minute is Y and second is Z.
        # E.g. Every month at 10:15:00
        self.at_time = datetime.time(**params)


def executor():
    print("Executor is running...")


s = TScheduler()
# s.create_every(1).day.do(executor)
# # s.create_every(15).days.do(executor)
# # s.create_every(1).monday.do(executor)
# # s.create_every(1).month.do(executor)
# s.create_every(10).days.at(H(hour=12)).do(executor)
# s.create_every(1).day.at(H(hour=12, minute=30)).do(executor)
s.create_every(1).january.do(executor)

# # while True:
# #     s.run_pending()

# h = H(hour=12, minute=30, second=0)
# h.unit = TimeUnit.SECONDS
# h.resolve(at_time=datetime.datetime.now(pytz.timezone('Europe/Paris')))
# print(h.at_time)
# print(h)
