import asyncio
import datetime
import time

import pytest

from simplecron import exceptions, utils
from simplecron.base import BaseScheduler, Job, Cancel


async def async_executor(job: Job):
    """An async executor function that runs the job's function."""
    print(f"Executing job: {job._get_label()}")
    await asyncio.sleep(0.1)  # Simulate some async work
    return None


def executor(job: Job):
    """A simple executor function that runs the job's function."""
    print(f"Executing job: {job._get_label()}")


def cancelled_executor(job: Job):
    """An executor function that cancels the job."""
    print(f"Cancelling job: {job._get_label()}")
    return Cancel(job, reason="Cancelled by executor")


def simple_before_listener(job: Job):
    """A simple before listener that prints a message before the job runs."""
    print(f"Before running job: {job._get_label()}")


def simple_after_listener(job: Job):
    """A simple after listener that prints a message after the job runs."""
    print(f"After running job: {job._get_label()}")


def simple_before_all_listener(jobs: list[Job]):
    """A simple before all listener that prints a message before all jobs run."""
    print(f"Before running all jobs: {[job._get_label() for job in jobs]}")


class TestBaseScheduler:
    def test_add_job(self):
        s = BaseScheduler()

        s.create_every(1).minutes.do(executor)
        s.create_every(2).minutes.do(executor)

        assert len(s.jobs()) == 2

    def test_run_pending_jobs(self):
        s = BaseScheduler()

        j1 = s.create_every(1).seconds.do(executor)
        time.sleep(1.5)  # Wait for the job to be debugged and executed

        s.run_pending()

        assert j1.was_executed is True

    def test_run_pending_job_cancels(self):
        s = BaseScheduler()

        s.create_every(1).seconds.do(cancelled_executor)
        time.sleep(1.5)  # Wait for the job to be debugged and executed
        s.run_pending()

        assert len(s._jobs) == 0

    def test_run_all_jobs(self):
        s = BaseScheduler()

        s.create_every(1).minutes.do(executor)
        s.run_all()

    def test_clear_jobs(self):
        s = BaseScheduler()
        s.create_every(1).minutes.do(executor)
        s.create_every(2).minutes.do(executor)

        s.clear()

        assert len(s._jobs) == 0

    def test_create_every(self):
        s = BaseScheduler()
        # Works like a chain:
        # new job (every(5)) -> minutes (updates job."unit") -> do(adds the job to the scheduler))
        job = s.create_every(5).minutes.do(executor)

        assert job is not None
        assert isinstance(job, Job)
        assert len(s._jobs) == 1

    def test_repr(self):
        s = BaseScheduler()
        s.create_every(1).minutes.do(executor)

        repr_str = repr(s)
        assert isinstance(repr_str, str)
        assert "BaseScheduler" in repr_str
        assert "jobs=1" in repr_str

    def test_cancel_job(self):
        s = BaseScheduler()
        s.create_every(1).minutes.do(cancelled_executor)
        s._cancel_job(s._jobs[0])

        assert len(s._jobs) == 0

    def test_with_event_listener(self):
        # Test that with_event_listener() correctly attaches an event listener to a job
        pass

    def test_with_context(self):
        # Test that with_context() correctly attaches context to a job
        pass

    def test_with_memory(self):
        # Test that with_memory() correctly attaches memory to a job
        pass

    def test_get_next_run(self):
        s = BaseScheduler()

        s.create_every(1).minutes.do(executor)
        s.create_every(2).minutes.do(executor)

        next_run = s.get_next_run()

        assert next_run is not None
        assert isinstance(next_run, datetime.datetime)

        # With tags

        s.create_every(30).minutes.do(executor).tags("tag1")

        assert s.get_next_run(tag="tag1") is not None

        # No jobs
        s._jobs.clear()

        assert s.get_next_run() is None

    def test_remaining_seconds(self):
        s = BaseScheduler()

        s.create_every(1).minutes.do(executor)

        remaining = s.remaining_seconds()

        assert remaining is not None
        assert isinstance(remaining, (int, float))
        assert remaining > 0

        # No next run

        s._jobs.clear()

        assert s.remaining_seconds() is None

    def test_run_all_jobs_with_listeners(self):
        s = BaseScheduler()

        s.with_event_listener(
            utils.EventListenerEnum.BEFORE,
            simple_before_listener

        )
        s.with_event_listener(
            utils.EventListenerEnum.AFTER,
            simple_after_listener
        )
        s.with_event_listener(
            utils.EventListenerEnum.BEFORE_ALL,
            simple_before_all_listener
        )

        # Create a job with an event listener
        s.create_every(1).seconds.do(executor)
        time.sleep(1.5)  # Wait for the job to be debugged and was_executed

        # Run pending jobs
        s.run_pending()

        for _, listeners in s.event_listeners.items():
            for listener in listeners:
                assert listener.counter > 0

    def test_calling_order(self):
        s = BaseScheduler()

        # Calling `do` without calling the unit property
        # should raise an IntervalError
        with pytest.raises(Exception):
            s.create_every(1).do(executor)

        s.create_every(1).minute.do(executor)

        # Correct calling order: every -> unit -> do
        s.create_every(1).minutes.do(executor)

    def test_async_job_execution(self):
        s = BaseScheduler()

        # Create an async job
        s.create_every(1).seconds.do(async_executor)
        time.sleep(1.5)  # Wait for the job to be debugged and executed

        # Run pending jobs
        s.run_pending()

        # Check if the job was executed
        assert s._jobs[0].was_executed is True
