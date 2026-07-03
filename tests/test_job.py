import pytest
from simplecron.base import Job, TimeUnit
from simplecron import exceptions
import datetime


class TestJob:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.job_instance = Job(interval=10)

    def test_utc_offset_correction(self):
        # Test that _utc_offset_correction correctly adjusts the datetime based on the job's timezone
        pass

    def test_schedule_next_run(self):
        self.job_instance.unit = TimeUnit.MINUTES.value
        self.job_instance._schedule_next_run()

        assert self.job_instance.next_run is not None
        assert (
            self.job_instance.next_run > datetime.datetime.now(
                self.job_instance.at_timezone)
        )

    def test_do(self):
        # Test that do() correctly assigns the job function and schedules the next run
        pass

    def test_run(self):
        # Test that run() executes the job function and updates last_run and next_run
        pass


class TestJobExceptions:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.job_instance = Job(interval=10)

    def test_interval_error(self):
        # Test that IntervalError is raised for invalid intervals
        pass

    def test_scheduler_not_found_error(self):
        # Test that SchedulerNotFoundError is raised when a job is created without an associated scheduler
        pass

    def test_schedule_next_run_no_unit(self):
        with pytest.raises(ValueError):
            self.job_instance.unit = None
            self.job_instance._schedule_next_run()
