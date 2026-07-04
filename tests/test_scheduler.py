from simplecron.base import BaseScheduler, Job, Cancel


class TestBaseScheduler:
    def test_add_job(self):
        s = BaseScheduler()

        s.create_every(1).minutes.do(lambda: print("Job executed"))
        s.create_every(2).minutes.do(lambda: print("Another job executed"))

        assert len(s.jobs()) == 4

    def test_run_pending_jobs(self):
        s = BaseScheduler()
        s.create_every(1).minutes.do(lambda: print("Job executed"))
        s.run_pending()

    def test_run_pending_job_cancels(self):
        s = BaseScheduler()

        def cancel_job():
            return Cancel()

        s.create_every(1).minutes.do(cancel_job)
        s.run_pending()

        assert len(s.jobs()) == 0

    def test_run_all_jobs(self):
        s = BaseScheduler()

        s.create_every(1).minutes.do(lambda j: print("Job executed"))
        s.run_all()

    def test_clear_jobs(self):
        # Test that clear_jobs() removes all scheduled jobs
        pass

    def test_create_every_job(self):
        # Test that create_every() correctly creates a job with the specified interval
        pass

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
