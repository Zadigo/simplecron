import datetime

import pytest

from simplecron.base import Job
from simplecron.utils import TimeUnit
from simplecron.base import BaseScheduler


def callback(job: Job):
    print(f"Job {job} executed!")


@pytest.fixture
def job():
    return BaseScheduler()


@pytest.fixture
def scheduler() -> BaseScheduler:
    return BaseScheduler()


def test_second(scheduler):
    j = scheduler.create_every(1).second.do(callback)

    assert j.unit == TimeUnit.SECONDS.value
    assert j._get_label() == "every 1 second"


def test_seconds(scheduler):
    j = scheduler.create_every(15).seconds.do(callback)

    assert j.unit == TimeUnit.SECONDS.value
    assert j._get_label() == "every 15 seconds"


def test_minute(scheduler):
    j = scheduler.create_every(1).minute.do(callback)

    assert j.unit == TimeUnit.MINUTES.value
    assert j._get_label() == "every 1 minute"


def test_minutes(scheduler):
    j = scheduler.create_every(15).minutes.do(callback)

    assert j.unit == TimeUnit.MINUTES.value
    assert j._get_label() == "every 15 minutes"


def test_hour(scheduler):
    j = scheduler.create_every(1).hour.do(callback)

    assert j.unit == TimeUnit.HOURS.value
    assert j._get_label() == "every 1 hour"


def test_hours(scheduler):
    j = scheduler.create_every(15).hours.do(callback)

    assert j.unit == TimeUnit.HOURS.value
    assert j._get_label() == "every 15 hours"


class TestDaily:
    """Daily jobs are jobs that will run every day, 
    at the time the job was created."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.scheduler = BaseScheduler()

    def test_day(self):
        j = self.scheduler.create_every(1).day.do(callback)

        assert j.unit == TimeUnit.DAYS.value
        assert j._get_label() == "every 1 day"

        next_run = datetime.datetime.now() + datetime.timedelta(days=1)
        assert j.next_run.date() == next_run.date()

    def test_days(self):
        j = self.scheduler.create_every(15).days.do(callback)

        assert j.unit == TimeUnit.DAYS.value
        assert j._get_label() == "every 15 days"


class TestWeekly:
    """Weekly jobs are jobs that will run every week,
    using the day of the week at the time the job was created. 
    If created at 14:30 on a Monday, it will run every
    Monday at 14:30."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.scheduler = BaseScheduler()

    def test_week(self):
        j = self.scheduler.create_every(1).week.do(callback)

        assert j.unit == TimeUnit.WEEKS.value
        assert j._get_label() == "every 1 week"

        next_run = datetime.datetime.now() + datetime.timedelta(weeks=1)
        assert j.next_run.date() == next_run.date()

    def test_weeks(self):
        j = self.scheduler.create_every(15).weeks.do(callback)

        assert j.unit == TimeUnit.WEEKS.value
        assert j._get_label() == "every 15 weeks"

    def test_other(self):
        """These specific categories of weekly job that
        are run a specific day of the week, like every Monday"""
        monday = self.scheduler.create_every(1).monday.do(callback)
        tuesday = self.scheduler.create_every(1).tuesday.do(callback)
        wednesday = self.scheduler.create_every(1).wednesday.do(callback)
        thursday = self.scheduler.create_every(1).thursday.do(callback)
        friday = self.scheduler.create_every(1).friday.do(callback)
        saturday = self.scheduler.create_every(1).saturday.do(callback)
        sunday = self.scheduler.create_every(1).sunday.do(callback)

        current_date = datetime.datetime.now()
        days = (7 - current_date.weekday())
        next_monday = current_date + datetime.timedelta(days=days)
        assert monday.next_run.date() == next_monday.date()

        def calc_days(value: int):
            return (value - current_date.weekday() + 7) % 7

        next_tuesday = current_date + datetime.timedelta(days=calc_days(1))
        assert tuesday.next_run.date() == next_tuesday.date()

        next_wednesday = current_date + datetime.timedelta(days=calc_days(2))
        assert wednesday.next_run.date() == next_wednesday.date()

        next_thursday = current_date + datetime.timedelta(days=calc_days(3))
        assert thursday.next_run.date() == next_thursday.date()

        next_friday = current_date + datetime.timedelta(days=calc_days(4))
        assert friday.next_run.date() == next_friday.date()

        # If the weekday is the current day, the job starts immediately (we tested this on a saturday)
        # next_saturday = current_date + datetime.timedelta(days=calc_days(5))
        # assert saturday.next_run.date() == next_saturday.date()

        next_sunday = current_date + datetime.timedelta(days=calc_days(6))
        assert sunday.next_run.date() == next_sunday.date()
