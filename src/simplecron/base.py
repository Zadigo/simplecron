import datetime
import functools
import inspect
import json
import random
import time
import uuid
from collections import defaultdict
from functools import total_ordering
from typing import Any, Callable, Optional, Sequence
from warnings import warn

import pytz

from src.simplecron import exceptions, utils
from src.simplecron.context import Context
from src.simplecron.providers import JobNotificationMessage, Provider
from src.simplecron.typings import (
    TypeDatetimes,
    TypeEventListenerCallback,
    TypeJobFunction,
    TypeJobReturn,
)
from src.simplecron.utils import logger


class Cancel:
    """A class representing a cancellation signal for jobs.

    This class is used to indicate that a job should be canceled. It can be returned from a job function
    to signal that the job should not be rescheduled::

        def my_job(job: Job):
            if some_condition:
                return Cancel(job)  # Signal to cancel the job
    """

    def __init__(
        self,
        job: "Job",
        reason: str = None,
        cancel_callback: Optional[Callable[["Job"], None]] = None,
    ):
        self.job = job
        self.reason = reason

        if not self.job.is_cancelled:
            self.job.is_cancelled = True

        if cancel_callback is not None:
            cancel_callback(self.job)


class Listener:
    """A class representing an event listener for a specific job event.
    It wraps a callback function that is triggered on specific job events.

    Attributes:
        event (str): The name of the event this listener is associated with.
        callback (Callable[["Job" | Sequence["Job"]], None]): The callback function to be executed when the event is triggered.
        counter (int): A counter tracking how many times the listener has been invoked.
        for_tags (Optional[set[str]]): A set of tags that this listener is associated with.
            If specified, the listener will only be triggered for jobs matching these tags. This does not apply
            to the `before_all` event, which is triggered for all jobs regardless of their tags.
    """

    def __init__(
        self,
        event: str,
        callback: Callable[["Job" | Sequence["Job"]], None],
        for_tags: Optional[set[str]] = None,
    ):
        self.event = event
        self.callback = callback
        self.counter: int = 0
        self.for_tags = for_tags

    def __repr__(self):
        return f"<Listener(event={self.event}, counter={self.counter})>"

    def __eq__(self, other: "Listener"):
        if not isinstance(other, Listener):
            return NotImplemented
        return self.event == other.event and self.callback == other.callback

    def resolve(self, jobs: Sequence["Job"]):
        try:
            if self.event == utils.EventListenerEnum.BEFORE_ALL.value:
                self.callback(jobs)
            else:
                for job in jobs:
                    if self.for_tags is not None:
                        if not job.has_tags(*list(self.for_tags)):
                            continue
                    self.callback(job)
        except Exception as e:
            # Catch any exceptions created by the user
            # coding mistakes without breaking the the main loop
            logger.error(f"Error in listener for event '{self.event}': {e}")

        self.counter += 1


class BaseScheduler:
    """A base class for the Simplecron scheduler.

    This class provides the core functionality for managing and executing scheduled jobs.
    It handles job creation, cancellation, and event listener resolution.

    Attributes:
        _jobs (list["Job"]): A list of all scheduled jobs.
        event_listeners (defaultdict): A dictionary mapping event names to their listeners.
        context (Context | None): The context object attached to the scheduler, if any.
    """

    def __init__(self):
        logger.info(f"Initializing Simplecron {self.__class__.__name__} scheduler...")

        self._jobs: list["Job"] = []
        self.event_listeners = defaultdict(list[Listener])
        self.context: Context | None = None
        self.providers = Provider(self)
        self.scheduler_uuid = uuid.uuid4()

        self.base_context = Context(scheduler_uuid=str(self.scheduler_uuid))

        logger.info(f"Scheduler UUID is: {self.scheduler_uuid}")

    def __repr__(self):
        return f"<BaseScheduler(jobs={len(self._jobs)})>"

    def _resolve_listeners(self, jobs: Sequence["Job"], *listeners: Listener):
        for listener in listeners:
            listener.resolve(jobs)

    def _run_job(self, job: "Job"):
        """Entry point for running a single job.

        Args:
            job (Job): The job to be executed.
        """
        # Resolve event that occurs before the job is run
        listeners = self.event_listeners[utils.EventListenerEnum.BEFORE.value]
        self._resolve_listeners([job], *listeners)

        result = job.run()
        logger.info(f"Job executed: {job}")
        if isinstance(result, Cancel):
            self._cancel_job(job)

        # Resolve event that occurs after the job is run
        listeners = self.event_listeners[utils.EventListenerEnum.AFTER.value]
        self._resolve_listeners([job], *listeners)

    def _cancel_job(self, job: "Job", cancel_result: Cancel):
        if job in self._jobs:
            self._jobs.remove(job)
            logger.warning(
                f"Job cancelled: {job}. Reason: {cancel_result.reason}"
            )

    def jobs(self, *tags: str) -> list["Job"]:
        if tags:
            return list(filter(lambda job: job.has_tags(*tags), self._jobs))
        return self._jobs

    def run_pending(self, context: dict[str, Any] = None):
        """Run all jobs that are scheduled to run at the current time."""
        if context is not None:
            self.base_context.json_data = self.base_context.json_data or {}
            self.base_context.json_data.update(context)

        _jobs = sorted(filter(lambda job: job.should_run, self._jobs))

        # Resolve listerners before all jobs are run
        listeners = self.event_listeners[utils.EventListenerEnum.BEFORE_ALL.value]
        self._resolve_listeners(_jobs, *listeners)

        for job in _jobs:
            self._run_job(job)

    def run_all(self):
        for job in self._jobs:
            self._run_job(job)

    def clear(self):
        """Clear all scheduled jobs."""
        self._jobs.clear()

    def create_every(self, interval: int, tag: str = None) -> "Job":
        job = Job(interval, self)
        if tag:
            job._tags.add(tag)
        return job

    def get_next_run(self, tag: str = None) -> Optional[datetime.datetime]:
        if not self._jobs:
            return None

        if tag is not None:
            _jobs = self.jobs(tag)
        else:
            _jobs = self._jobs

        return min(_jobs).next_run if _jobs else None

    def remaining_seconds(self):
        """Returns the number of seconds until the next scheduled job is due to run."""
        next_run = self.get_next_run()

        if not next_run:
            return None

        now = datetime.datetime.now(next_run.tzinfo or datetime.UTC)
        return max(0, (next_run - now).total_seconds())

    def with_event_listener(
        self,
        event: utils.EventListenerEnum,
        callback: TypeEventListenerCallback,
        for_tags: Optional[Sequence[str]] = None,
    ):
        """Attaches a callback function to a specific event listener. There are three types of event listeners available:

        - `BEFORE`: Triggered before each job is run.
        - `AFTER`: Triggered after each job is run.
        - `BEFORE_ALL`: Triggered before all jobs are run in a batch.

        For example, to attach a callback that logs information before each job runs, you can do the following::

            def log_before_jobs(jobs):
                for job in jobs:
                    print(f"About to run job: {job}")

            default_scheduler.with_event_listener(utils.EventListenerEnum.BEFORE, log_before_jobs)

        Args:
            event (utils.EventListenerEnum): The event listener type to attach the callback to.
            callback (Callable[[Sequence["Job"]], None]): The callback function to be executed when the event is triggered. It receives a sequence of jobs as its argument.
        """
        if event.value not in utils.EVENT_LISTENERS:
            raise ValueError(
                f"Invalid event listener: {event}. Must be one of {list(utils.EVENT_LISTENERS)}."
            )

        self.event_listeners[event.value].append(
            Listener(event.value, callback, for_tags)
        )

    def before_all_events(self, callbacks: Sequence[TypeEventListenerCallback]):
        """Attach multiple callback functions to the BEFORE_ALL event listener.

        Args:
            callbacks (Sequence[TypeEventListenerCallback]): A sequence of callback functions to be attached to the BEFORE_ALL event listener.
        """
        for callback in callbacks:
            self.with_event_listener(utils.EventListenerEnum.BEFORE_ALL, callback)

    def before_events(
        self,
        callbacks: Sequence[TypeEventListenerCallback],
        for_tags: Optional[Sequence[str]] = None,
    ):
        """Attach multiple callback functions to the BEFORE event listener.

        Args:
            callbacks (Sequence[TypeEventListenerCallback]): A sequence of callback functions to be attached to the BEFORE event listener.
        """
        for callback in callbacks:
            self.with_event_listener(utils.EventListenerEnum.BEFORE, callback, for_tags)

    def after_events(
        self,
        callbacks: Sequence[TypeEventListenerCallback],
        for_tags: Optional[Sequence[str]] = None,
    ):
        """Attach multiple callback functions to the AFTER event listener.

        Args:
            callbacks (Sequence[TypeEventListenerCallback]): A sequence of callback functions to be attached to the AFTER event listener.
        """
        for callback in callbacks:
            self.with_event_listener(utils.EventListenerEnum.AFTER, callback, for_tags)

    def with_context(self, context: Context):
        """Replace the existing context of the scheduler with a new one.

        Args:
            context (Context): The context object to be attached to the scheduler.
        """
        if context.scheduler_uuid is None:
            context.scheduler_uuid = str(self.scheduler_uuid)

        if context.json_data is not None:
            self.base_context.json_data.update(context.json_data)


default_scheduler = BaseScheduler()


@total_ordering
class Job:
    """A periodic job that can be scheduled to run at specific intervals.

    Args:
        internal (int): The interval in seconds at which the job should run.
        scheduler (Optional[BaseScheduler]): The scheduler instance to which the job belongs. If not provided, the default scheduler will be used.

    Attributes:
        interval (int): The interval in seconds at which the job should run.
        scheduler (Optional[BaseScheduler]): The scheduler instance to which the job belongs. If not provided, the default scheduler will be used.
        _job_func (TypeJobFunction): The function to be executed when the job runs. It can be a callable or a Job instance.
        latest (Optional[datetime.time]): The latest time at which the job should run (if specified).
        unit (Optional[str]): The unit of time for the job's interval (e.g., seconds, minutes, hours).
        at_time (Optional[datetime.time]): The time at which the job should run (if specified).
        at_timezone (Optional[datetime.timezone]): An optional timezone for the job's scheduled time.
        last_run (Optional[datetime.datetime]): The datetime of the last time the job was run.
        next_run (Optional[datetime.datetime]): The next scheduled run time for the job.
        start_day (Optional[str]): The weekday on which the job should run (if specified) for example when using "every week on tuesday", the start day would be "tuesday".
        cancel_after (Optional[datetime.datetime]): An optional time of final run.
        tags (set[str]): A set of tags associated with the job.
        job_uuid (uuid.UUID): A unique identifier for the job, used for tracking and management.
        is_cancelled (bool): A flag indicating whether the job has been cancelled.
        was_executed (bool): A flag indicating whether the job has been executed at least once.
    """

    label_template = "every {interval} {unit} at {at_time}"

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
        # If specified, the weekday on which the job should run
        # (for example when using "every week on tuesday",
        # the start day would be "tuesday")
        self.start_day: Optional[str] = None
        # Optional time of final run
        self.cancel_after: Optional[datetime.datetime] = None

        self._tags: set[str] = set()
        # Unique identifier for the job, used for tracking and management
        self.job_uuid = uuid.uuid4()
        # Indicates whether the job has been cancelled.
        # If True, the job will not be rescheduled after its next run.
        self.is_cancelled = False
        # Indicates whether the job has been executed. If True, the job has already run at least once.
        self.was_executed = False

    def __repr__(self):
        return f"<Job([{self._get_label(as_slug=True)}], next_run={self.next_run})>"

    def __lt__(self, other: "Job"):
        if not isinstance(other, Job):
            return NotImplemented
        return self.next_run < other.next_run

    def __eq__(self, other: "Job"):
        if not isinstance(other, Job):
            return NotImplemented
        return self.next_run == other.next_run

    def __hash__(self):
        tags = tuple(sorted(self._tags))
        return hash((self.job_uuid, self._get_label(as_slug=True), *tags))

    @property
    def get_current_time(self) -> datetime.datetime:
        """Get the current time in the job's timezone or UTC if no timezone is set."""
        return datetime.datetime.now(self.get_timezone)

    @property
    def get_timezone(self) -> datetime.timezone:
        """Get the timezone of the job or UTC if no timezone is set."""
        self.at_timezone = self.at_timezone or datetime.timezone.utc
        return self.at_timezone

    @property
    def should_run(self) -> bool:
        if self.next_run is None:
            return False

        # Determine the timezone to use for comparison. If the job has a specific
        # timezone set, use that; otherwise, default to UTC.
        timezone = self.next_run.tzinfo or self.at_timezone or datetime.timezone.utc
        return datetime.datetime.now(timezone) >= self.next_run

    @property
    def second(self) -> "Job":
        if self.interval != 1:
            raise exceptions.IntervalError(self.interval, expected="equal to 1")
        return self.seconds

    @property
    def seconds(self) -> "Job":
        self.unit = utils.TimeUnit.SECONDS.value
        return self

    @property
    def minute(self) -> "Job":
        if self.interval != 1:
            raise exceptions.IntervalError(self.interval, expected="equal to 1")
        return self.minutes

    @property
    def minutes(self) -> "Job":
        self.unit = utils.TimeUnit.MINUTES.value
        return self

    @property
    def hour(self) -> "Job":
        if self.interval != 1:
            raise exceptions.IntervalError(self.interval, expected="equal to 1")
        return self.hours

    @property
    def hours(self) -> "Job":
        self.unit = utils.TimeUnit.HOURS.value
        return self

    @property
    def day(self) -> "Job":
        if self.interval != 1:
            raise exceptions.IntervalError(self.interval, expected="equal to 1")
        return self.days

    @property
    def days(self) -> "Job":
        self.unit = utils.TimeUnit.DAYS.value
        return self

    @property
    def week(self) -> "Job":
        if self.interval != 1:
            raise exceptions.IntervalError(self.interval, expected="equal to 1")
        return self.weeks

    @property
    def weeks(self) -> "Job":
        self.unit = utils.TimeUnit.WEEKS.value
        return self

    @property
    def monday(self) -> "Job":
        if self.interval != 1:
            raise exceptions.IntervalError(self.interval, expected="equal to 1")
        self.start_day = "monday"
        return self.weeks

    @property
    def tuesday(self) -> "Job":
        if self.interval != 1:
            raise exceptions.IntervalError(self.interval, expected="equal to 1")
        self.start_day = "tuesday"
        return self.weeks

    @property
    def wednesday(self) -> "Job":
        if self.interval != 1:
            raise exceptions.IntervalError(self.interval, expected="equal to 1")
        self.start_day = "wednesday"
        return self.weeks

    @property
    def thursday(self) -> "Job":
        if self.interval != 1:
            raise exceptions.IntervalError(self.interval, expected="equal to 1")
        self.start_day = "thursday"
        return self.weeks

    @property
    def friday(self) -> "Job":
        if self.interval != 1:
            raise exceptions.IntervalError(self.interval, expected="equal to 1")
        self.start_day = "friday"
        return self.weeks

    @property
    def saturday(self) -> "Job":
        if self.interval != 1:
            raise exceptions.IntervalError(self.interval, expected="equal to 1")
        self.start_day = "saturday"
        return self.weeks

    @property
    def sunday(self) -> "Job":
        if self.interval != 1:
            raise exceptions.IntervalError(self.interval, expected="equal to 1")
        self.start_day = "sunday"
        return self.weeks

    @classmethod
    def build_from_dict(cls, data: dict) -> "Job":
        """Reconstruct a Job instance from a dictionary representation.

        Args:
            data (dict): A dictionary containing the job's attributes.
        """
        interval = data.pop("interval")
        job = cls(interval)
        job.__dict__.update(data)
        return job

    def _must_cancel(self) -> bool:
        """Determine if the job should be cancelled based on its 'cancel_after' attribute.

        Returns:
            bool: True if the job should be cancelled, False otherwise.
        """
        if self.cancel_after is None:
            return False

        return self.get_current_time >= self.cancel_after

    def _get_label(self, as_slug: bool = False) -> str:
        """Generate a human-readable label for the job, describing its schedule."""
        if self.at_time is not None:
            text = self.label_template.format(
                interval=self.interval,
                unit=self.unit,
                at_time=self.at_time.strftime("%H:%M:%S"),
            )
        else:
            _unit = self.unit
            if (self.interval is not None and self.interval == 1) and _unit is not None:
                _unit = _unit.removesuffix("s")
            text = f"every {self.interval} {_unit}"

        if as_slug:
            return text.replace(" ", "-").lower()
        return text

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

        params = {"second": self.at_time.second, "microsecond": 0}

        if self.unit == utils.TimeUnit.DAYS.value or self.start_day is not None:
            params.update(hour=self.at_time.hour, minute=self.at_time.minute)

        if (
            self.unit == utils.TimeUnit.DAYS.value
            or self.unit == utils.TimeUnit.HOURS.value
            or self.start_day is not None
        ):
            params.update(minute=self.at_time.minute)

        new_dt = dt.replace(**params)
        corrected_dt = self._utc_offset_correction(new_dt, restore_time=True)
        return corrected_dt

    def _utc_offset_correction(
        self, dt: datetime.datetime, restore_time: bool = False
    ) -> datetime.datetime:
        """Function that corrects the UTC offset of a datetime object responding to the
        the problem of when the UTC offset changes because of daylight saving time (DST), should
        the actual instant time be preserves or the local clock time be preserved instead.

        So if a clock was set at 2:30 AM, with a UTC offset changes from -5 to -4, the function
        will correct the datetime to 3:30 AM, preserving the local clock time.

        Args:
            dt (datetime.datetime): The datetime to be corrected.
            restore_time (bool): If True, the function will attempt to restore the original wall-clock time after correcting the UTC offset. Defaults to False.
        """
        # Remember the original UTC offset
        before_value = dt.utcoffset() or 0

        # Convert ("normalize") into the target timezone
        moment = dt.astimezone(self.get_timezone)
        after_value = moment.utcoffset() or 0

        # If there's no change,
        # return the original datetime
        if before_value == after_value:
            return moment

        if not restore_time:
            return moment

        # Compute how much the offset changed
        difference = after_value - before_value
        # Shift the datetime backwards
        moment -= difference

        if self.at_timezone is None:
            raise ValueError("at_timezone must be set for UTC offset correction.")

        # Check if the this local time actually valid.
        # If not move it to the closest valid time (DST Gap)
        # For example, if 02:23 does not exist (because DST
        # moves from 02:00 to 03:00), this will schedule the job at 03:23.
        renormalized_moment = self.get_timezone.normalize(moment)
        if renormalized_moment != moment:
            moment += difference
        return renormalized_moment

    def _schedule_next_run(self):
        """Calculate and set the next run time for the job based
        on its interval and unit."""
        if self.unit not in utils.TIME_UNITS:
            raise ValueError(
                f"Invalid time unit: {self.unit}. Must be one of {list(utils.TIME_UNITS)}. "
                "Before calling this method, you must call one of the unit propperties "
                "(e.g., seconds, minutes, hours, days, weeks) e.g., job.every(5).seconds.do(task)."
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
        current_time = datetime.datetime.now(self.get_timezone)
        _next_run = current_time

        if self.start_day is not None:
            if self.unit != utils.TimeUnit.WEEKS.value:
                raise exceptions.ScheduleValueError(self.unit)
            _next_run = utils.move_to_next_weekday(_next_run, self.start_day)

        # Delta to add to the current time to get the next run time
        period = datetime.timedelta(**{self.unit: _interval})

        # If the interval is not 1, we need to
        # add the period to the next run time
        if _interval != 1:
            _next_run += period

        # In the case where the next run time is in the past,
        # we need to keep adding the period so that the next run
        # time is in the future
        while _next_run <= current_time:
            _next_run += period

        self.next_run = self._utc_offset_correction(
            _next_run, restore_time=self.at_time is not None
        )

    def destructure(self, str_json: bool = False) -> dict[str, str] | str:
        """Destructure the job instance into a
        dictionary representation that can be easily serialized."""
        values: dict[str, str] = {}

        for key, value in self.__dict__.items():
            if key.startswith("__"):
                continue

            if callable(value):
                values[key] = value.__name__
                continue

            if isinstance(value, (datetime.datetime, datetime.time)):
                values[key] = value.isoformat()
                continue

            if isinstance(value, BaseScheduler):
                values[key] = value.__class__.__name__
                continue

            if key == "_tags":
                values[key] = ",".join(value)
                continue

            if value is None:
                values[key] = ""
                continue

            values[key] = str(value)

        if str_json:
            return json.dumps(values)

        return values

    def tags(self, *tags: str) -> "Job":
        """Add tags to the job for categorization and filtering."""
        for tag in tags:
            if not isinstance(tag, str):
                raise TypeError(f"Tag must be a string, got {type(tag)}")

        self._tags.update(tags)
        return self

    def has_tags(self, *tags: str) -> bool:
        """Check if the job has any of the specified tags.

        Args:
            *tags (str): Tags to check against the job's tags.

        Returns:
            bool: True if the job has any of the specified tags, False otherwise.
        """
        tags_to_check = set(tags)
        matching_tags = self._tags.intersection(tags_to_check)
        return bool(matching_tags)

    def do(self, job_func: TypeJobFunction, *args, **kwargs) -> "Job":
        """Assign a function to be executed when the job runs

        ## Examples

        .. code-block:: python
            import simplecron

            simplecron.every(10).seconds.do(my_job_function)

            while True:
                simplecron.run_pending()

        Args:
            job_func (TypeJobFunction): The function to be executed when the job runs.
            *args: Positional arguments to pass to the job function.
            **kwargs: Keyword arguments to pass to the job function.

        Returns:
            Job: The current Job instance, allowing for method chaining.

        Raises:
            SchedulerNotFoundError: If the job is created without an associated scheduler.
        """
        self._job_func = functools.partial(job_func, *args, **kwargs)
        functools.update_wrapper(self._job_func, job_func)
        self._schedule_next_run()

        if self.scheduler is None:
            raise exceptions.SchedulerNotFoundError()

        self.scheduler._jobs.append(self)
        logger.info("Job scheduled to start at %s", self.next_run)
        return self

    # async def async_do(self, job_func: TypeAsyncJobFunction, *args, **kwargs) -> "Job":
    #     """Assign an asynchronous function to be executed when the job runs.

    #     Args:
    #         job_func (TypeAsyncJobFunction): The asynchronous function to be executed when the job runs.
    #         *args: Positional arguments to pass to the job function.
    #         **kwargs: Keyword arguments to pass to the job function.

    #     Returns:
    #         Job: The current Job instance, allowing for method chaining.

    #     Raises:
    #         SchedulerNotFoundError: If the job is created without an associated scheduler.

    #     Example::

    #         import simplecron

    #         simplecron.every(10).seconds.async_do(my_async_job_function)

    #         while True:
    #             simplecron.run_pending()
    #     """
    #     self._job_func = functools.partial(job_func, *args, **kwargs)
    #     functools.update_wrapper(self._job_func, job_func)

    #     if self.scheduler is None:
    #         raise exceptions.SchedulerNotFoundError()

    #     self.scheduler._jobs.append(self)
    #     return self

    def at(
        self,
        using: datetime.time,
        timezone: Optional[datetime.timezone | pytz.BaseTzInfo] = None,
    ) -> "Job":
        """Set a time at which the job should run.

        ## Example

        To schedule a job to run every day specifically at `14:30`, you can use the following code::

            import datetime
            import simplecron

            simplecron.every(1).days.at(datetime.time(hour=14, minute=30)).do(my_job_function)

        To schedule a job to run every hour when the minute is 15 e.g. 10:15, 11:15, 12:15::

            import datetime
            import pytz
            import simplecron

            timezone = pytz.timezone('America/New_York')
            simplecron.every(1).days.at(datetime.time(minute=30), timezone=timezone).do(my_job_function)

        To schedule a job to runs every minute when the second is 30 e.g. 10:15:30, 10:16:30, 10:17:30::

            import datetime
            import simplecron

            simplecron.every(1).hours.at(datetime.time(second=30)).do(my_job_function)

        Using `hours` and `minutes` units will fixate the time to the specified hour and minute. For instance, in the above
        example, the job will run every hour and ...

        Args:
            time (datetime.time): The time at which the job should run.
            timezone (Optional[datetime.timezone | pytz.BaseTzInfo]): An optional timezone for the job's scheduled time. Defaults to None.

        Returns:
            Job: The current Job instance, allowing for method chaining.
        """
        warn(
            "This method is not complete. Use with caution. The 'at' method is intended to set a specific time for the job to run, but it may not handle all edge cases correctly."
        )
        if (
            self.unit
            not in [
                utils.TimeUnit.DAYS.value,
                utils.TimeUnit.HOURS.value,
                utils.TimeUnit.MINUTES.value,
            ]
            and self.start_day is None
        ):
            raise exceptions.AtScheduleError(self.unit)

        if timezone is not None:
            if not isinstance(timezone, (pytz.BaseTzInfo, datetime.tzinfo)):
                raise ValueError(
                    f"Invalid timezone: {timezone}. Must be a pytz timezone instance or a datetime.tzinfo instance."
                )
            self.at_timezone = timezone

        hour: Optional[int] = None
        minute: Optional[int] = None
        second: Optional[int] = None

        # Every minute when the second is X.
        # E.g. 10:15:30, 10:16:30, 10:17:30
        if self.unit == utils.TimeUnit.MINUTES.value:
            hour = 0
            minute = 0
            second = using.second

        # Every day when the hour is X and the minute is Y.
        # E.g. Monday at 10:15:00, Tuesday at 10:15:00, Wednesday at 10:15:00
        if self.unit == utils.TimeUnit.DAYS.value or self.start_day:
            hour = using.hour
            minute = using.minute
            second = using.second

        # Every hour when the minute is X.
        # E.g. 10:15:00, 11:15:00, 12:15:00
        if self.unit == utils.TimeUnit.HOURS.value:
            hour = 0
            minute = 0
            second = using.second

        self.at_time = datetime.time(hour=hour, minute=minute, second=second)
        return self

    def until(self, limit: TypeDatetimes) -> "Job":
        """Set a limit for the job's execution, after which it will be cancelled.

        Args:
            limit (TypeDatetimes): The limit for the job's execution. Can be a datetime.datetime, datetime.time, or datetime.timedelta instance.
        """
        if isinstance(limit, datetime.datetime):
            self.cancel_after = limit

        if isinstance(limit, datetime.time):
            self.cancel_after = datetime.datetime.combine(
                self.get_current_time.date(), limit, tzinfo=self.at_timezone
            )

        if isinstance(limit, datetime.timedelta):
            self.cancel_after = self.get_current_time + limit

        if self.cancel_after is None:
            raise ValueError(
                f"Invalid limit type: {type(limit)}. Must be one of datetime.datetime, datetime.time, or datetime.timedelta."
            )

        if self.cancel_after <= self.get_current_time:
            raise ValueError(
                f"Invalid limit: {self.cancel_after}. Must be in the future."
            )

        return self

    def run(self) -> TypeJobReturn:
        """Run the job.

        Returns:
            TypeJobReturn: The result of the job execution or a Cancel instance if the job was cancelled.
        """
        if self._job_func is None:
            raise ValueError(
                "No job function assigned. Use the 'do' method to assign a function."
            )

        if self._must_cancel():
            return Cancel(
                self, reason=f"Job cancelled after {self.cancel_after.isoformat()}"
            )

        signature = inspect.signature(self._job_func)
        accepts_kwargs = any(
            p.kind == inspect.Parameter.VAR_KEYWORD
            for p in signature.parameters.values()
        )
        if not accepts_kwargs:
            raise ValueError("The job function must accept **kwargs.")

        result = self._job_func(self, context=self.scheduler.base_context)

        self.last_run = self.get_current_time
        self._schedule_next_run()

        if self._must_cancel():
            return Cancel(
                self, reason=f"Job cancelled after {self.cancel_after.isoformat()}"
            )

        self.was_executed = True
        self.scheduler.providers.notify(
            job=self,
            job_message=JobNotificationMessage(
                job_uuid=str(self.job_uuid),
                runned_at=str(self.get_current_time),
            ),
        )
        return result

    # async def async_run(self) -> TypeJobReturn:
    #     if self._job_func is None:
    #         raise ValueError(
    #             "No job function assigned. Use the 'do' method to assign a function."
    #         )

    #     if self._must_cancel():
    #         return Cancel(
    #             self, reason=f"Job cancelled after {self.cancel_after.isoformat()}"
    #         )

    #     aw = self._job_func(self)
    #     if not inspect.isawaitable(aw):
    #         raise ValueError(
    #             "The job function is not awaitable. Use the 'do' method to run a synchronous function."
    #         )

    #     def done_callback(t: asyncio.Task):
    #         self.last_run = self.get_current_time
    #         self._schedule_next_run()

    #         self.was_executed = True

    #     task = asyncio.create_task(aw)
    #     task.add_done_callback(done_callback)

    #     if self._must_cancel():
    #         return Cancel(
    #             self,
    #             reason=f"Job cancelled after {self.cancel_after.isoformat()}",
    #             cancel_callback=lambda job: task.cancel(),
    #         )

    #     return task


def every(interval: int, tag: Optional[str] = None) -> Job:
    """Creates a new job instance using the default scheduler. This function
    is a convenient way to create jobs without needing to directly interact
    with the scheduler.

    Args:
        interval (int): The interval in seconds at which the job should run.
        tag (str, optional): An optional tag to associate with the job. Defaults to None.

    Returns:
        Job: A new Job instance that can be configured and scheduled.
    """
    return default_scheduler.create_every(interval, tag)


def run_pending(context: dict[str, Any] = None):
    """Run all jobs created in the default scheduler."""
    default_scheduler.run_pending(context=context)


def start_blocking(**kwargs: Any):
    """Start the default scheduler in a blocking loop."""
    while True:
        default_scheduler.run_pending(**kwargs)
        time.sleep(1)
