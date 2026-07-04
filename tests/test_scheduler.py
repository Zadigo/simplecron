import datetime

from simplecron.base import BaseScheduler, Job, Cancel


def executor(job: Job):
    """A simple executor function that runs the job's function."""
    print(f"Executing job: {job._get_label()}")


def cancelled_executor(job: Job):
    """An executor function that cancels the job."""
    print(f"Cancelling job: {job._get_label()}")
    return Cancel(job, reason="Cancelled by executor")


class TestBaseScheduler:
    def test_add_job(self):
        s = BaseScheduler()

        s.create_every(1).minutes.do(executor)
        s.create_every(2).minutes.do(executor)

        assert len(s.jobs()) == 2

    def test_run_pending_jobs(self):
        s = BaseScheduler()
        s.create_every(1).minutes.do(executor)
        s.run_pending()

    def test_run_pending_job_cancels(self):
        s = BaseScheduler()

        s.create_every(1).seconds.do(cancelled_executor)
        s.run_pending()

        assert len(s._jobs) == 0

    def test_run_all_jobs(self):
        s = BaseScheduler()

        s.create_every(1).minutes.do(executor)
        s.run_all()

    def test_clear_jobs(self):
        # Test that clear_jobs() removes all scheduled jobs
        pass

    def test_create_every(self):
        s = BaseScheduler()
        # Works like a chain:
        # new job (every(5)) -> minutes (updates job."unit") -> do(adds the job to the scheduler))
        job = s.create_every(5).minutes.do(executor)

        assert job is not None
        assert isinstance(job, Job)
        assert len(s._jobs) == 1

    def test_get_next_run_job(self):
        # Test that get_next_run() returns the next scheduled job
        pass

    def test_schedule_job(self):
        # Test that schedule_job() correctly schedules a job
        pass

    def test_cancel_job(self):
        # Test that cancel_job() correctly cancels a scheduled job
        pass

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
        pass
