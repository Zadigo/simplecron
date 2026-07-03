import asyncio
import datetime
import functools
import random
import time
from typing import Callable, Optional
import uuid

from simplecron import exceptions
from simplecron.typings import TypeJobFunction
from simplecron import utils

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


class EventListener(enum.Enum):
    BEFORE_ALL = "before_all"
    BEFORE = "before"
    AFTER = "after"


class BaseScheduler:
    def __init__(self):
        self.jobs: list["Job"] = []

    def _run_job(self, job: "Job"):
        result = job.run()

    def jobs(self, tag: str = None) -> list["Job"]:
        pass

    def run_pending(self):
        """Run all jobs that are scheduled to run at the current time."""
        _jobs = sorted(filter(lambda job: job.should_run, self.jobs))
        for job in _jobs:
            self._run_job(job)

    def run_all(self):
        pass

    def clear(self):
        pass

    def create_every(self, interval: int, tag: str = None) -> "Job":
        return Job(interval, self)

    def get_next_run(self, tag: str = None) -> "Job":
        pass

    def with_event_listener(self, event: EventListener, callback: Callable[["Job"], None]):
        pass

    def with_context(self, context: dict):
        pass

    def with_memory(self, using: str):
        pass


default_scheduler = BaseScheduler()


class Job:
    """A periodic job that can be scheduled to run at specific intervals.

    Args:
        internal (int): The interval in seconds at which the job should run.
        scheduler (Optional[BaseScheduler]): The scheduler instance to which the job belongs. If not provided, the default scheduler will be used.
    """

    def __init__(self, interval: int, scheduler: Optional[BaseScheduler] = None):
        # The interval in seconds at which the job should run.
        self.interval = interval
        # The scheduler instance to which the job belongs. If not provided, the default scheduler will be used.
        self.scheduler = scheduler
        # The function to be executed when the job runs.
        # It can be a callable or a Job instance.
        self._job_func: TypeJobFunction = None
        # The latest time at which the job should run (if specified)
        self.latest: Optional[datetime.time] = None

        # The unit of time for the job's interval (e.g., seconds, minutes, hours)
        self.unit: Optional[str] = None
        # Time at which the job should run (if specified)
        self.at_time: Optional[datetime.time] = None
        # An optional timezone for the job's scheduled time
        self.at_timezone: Optional[datetime.timezone] = None
        # Datetime of the last time the job was run
        self.last_run: Optional[datetime.datetime] = None
        # The next scheduled run time for the job
        self.next_run: Optional[datetime.datetime] = None
        # Weekday on which the job should run (if specified) for example
        # when using "every week on tuesday", the start day would be "tuesday"
        self.start_day: Optional[str] = None
        # Optional time of final run
        self.cancel_after: Optional[datetime.datetime] = None

        self.tags: set[str] = set()
        # Scheduler instance to which the job belongs. If not provided, the default scheduler will be used.
        self.scheduler: Optional[BaseScheduler] = scheduler
        # Unique identifier for the job, used for tracking and management
        self.job_uuid = uuid.uuid4()

    def __repr__(self):
        return f"<Job(interval={self.interval}, unit={self.unit}, next_run={self.next_run})>"

    def __lt__(self, other: "Job"):
        if not isinstance(other, Job):
            return NotImplemented
        return self.next_run < other.next_run

    @property
    def should_run(self) -> bool:
        return datetime.datetime.now() >= self.next_run

    @property
    def second(self) -> "Job":
        if self.interval < 1:
            raise exceptions.IntervalError(self.interval)
        return self.seconds

    @property
    def seconds(self) -> "Job":
        self.unit = TimeUnit.SECONDS.value
        return self

    @property
    def minute(self) -> "Job":
        if self.interval < 1:
            raise exceptions.IntervalError(self.interval)
        return self.minutes

    @property
    def minutes(self) -> "Job":
        self.unit = TimeUnit.MINUTES.value
        return self

    def _move_to_at_time(self, dt: datetime.datetime) -> datetime.datetime:
        """Move the given datetime to the specified 'at_time' if it is set.

        ## Example

        With a job scheduled to run every day at `14:30`, if the current datetime is `2024-06-15 10:00`, 
        calling this method will return a datetime of `2024-06-15 14:30`.

        Args:
            dt (datetime.datetime): The original datetime.

        Returns:
            datetime.datetime: The adjusted datetime moved to the specified 'at_time' if set, otherwise the original datetime.
        """
        if self.at_time is None:
            return dt

        params = {
            'second': self.at_time.second,
            'microsecond': 0
        }

        if self.unit == TimeUnit.DAYS.value or self.start_day is not None:
            params.update(hour=self.at_time.hour)

        if self.unit == TimeUnit.DAYS.value or self.unit == TimeUnit.HOURS.value or self.start_day is not None:
            params.update(minute=self.at_time.minute)

        new_dt = dt.replace(**params)
        corrected_dt = self._utc_offset_correction(new_dt, fixate_time=True)
        return corrected_dt

    def _utc_offset_correction(self, dt: datetime.datetime, fixate_time: bool = False) -> datetime.datetime:
        """Adjust the given datetime to account for UTC offset based on the job's timezone."""
        # Normalize corrects the utc-offset to match the timezone
        # For example: When a date&time&offset does not exist within a timezone,
        # the normalization will change the utc-offset to where it is valid.
        # It does this while keeping the moment in time the same, by moving the
        # time component opposite of the utc-change.
        before_value = dt.utcoffset()
        moment = dt.astimezone(self.at_timezone)
        after_value = moment.utcoffset()

        # No change in utc-offset, return the original datetime
        if before_value == after_value:
            return moment

        if not fixate_time:
            return moment

        difference = after_value - before_value
        # Adjust the moment to fixate the time,
        # keeping the original time component intact
        moment -= difference
        renormalized_moment = self.at_timezone.normalize(moment)
        if renormalized_moment != after_value:
            # We ended up in a DST Gap. The requested 'at' time does not exist
            # within the current timezone/utc-offset. As a best effort, we will
            # schedule the job 1 offset later than possible.
            # For example, if 02:23 does not exist (because DST moves from 02:00
            # to 03:00), this will schedule the job at 03:23.
            moment += difference
        return renormalized_moment

    def _schedule_next_run(self):
        """Calculate and set the next run time for the job based 
        on its interval and unit."""
        if self.unit not in TIME_UNITS:
            raise ValueError(
                f"Invalid time unit: {self.unit}. Must be one of {list(TIME_UNITS)}."
            )

        _interval = self.interval
        if self.latest is not None:
            if not self.latest >= self.interval:
                raise exceptions.IntervalError(
                    self.interval, expected=f"less than or equal to {self.latest}"
                )
            _interval = random.randint(self.interval, self.latest)

        # Get the current time in the specified timezone,
        # or UTC if no timezone is set
        current_time = datetime.datetime.now(self.at_timezone)

        _next_run = current_time

        if self.start_day is not None:
            if self.unit != TimeUnit.WEEKS.value:
                raise exceptions.ScheduleValueError(self.unit)
            _next_run = utils.move_to_next_weekday(_next_run, self.start_day)

        if self.at_time is not None:
            _next_run = None

        # Calculate the next run time based on the interval and unit
        period = datetime.timedelta(**{self.unit: _interval})

        # If the interval is not 1, we need to a
        # dd the period to the next run time
        if _interval != 1:
            _next_run += period

        # Adjust the next run time to ensure it is in the future
        while _next_run <= current_time:
            _next_run += period

        self.next_run = _next_run

    def do(self, job_func: TypeJobFunction, *args, **kwargs) -> "Job":
        """Assign a function to be executed when the job runs

        Args:
            job_func (TypeJobFunction): The function to be executed when the job runs.
            *args: Positional arguments to pass to the job function.
            **kwargs: Keyword arguments to pass to the job function.

        Returns:
            Job: The current Job instance, allowing for method chaining.

        Raises:
            SchedulerNotFoundError: If the job is created without an associated scheduler.

        Example::

            import simplecron

            simplecron.every(10).seconds.do(my_job_function)

            while True:
                simplecron.run_pending()
        """

        self._job_func = functools.partial(job_func, *args, **kwargs)
        functools.update_wrapper(self._job_func, job_func)
        self._schedule_next_run()

        if self.scheduler is None:
            raise exceptions.SchedulerNotFoundError()

        self.scheduler.jobs.append(self)
        return self

    def run(self):
        if self._job_func is None:
            raise ValueError(
                "No job function assigned. Use the 'do' method to assign a function.")

        result = self._job_func(self)
        self.last_run = datetime.datetime.now()
        self._schedule_next_run()
        return result


def every(interval: int, tag: Optional[str] = None) -> Job:
    """Create a new job that runs at a specified interval.

    Args:
        interval (int): The interval in seconds at which the job should run.
        tag (str, optional): An optional tag to associate with the job. Defaults to None.

    Returns:
        Job: A new Job instance that can be configured and scheduled.
    """
    return default_scheduler.create_every(interval, tag)


def run_pending_jobs():
    """Run all jobs that are scheduled to run at the current time."""
    default_scheduler.run_pending()


class RunningScheduler:
    async def __call__(self, *jobs: "Job"):
        try:
            while True:
                run_pending_jobs()
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("Scheduler stopped.")
