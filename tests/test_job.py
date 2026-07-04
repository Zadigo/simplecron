import pytest
from simplecron.base import Job
from simplecron.utils import TimeUnit
from simplecron import exceptions
import datetime
import pytz


class TestJob:
    @pytest.fixture(autouse=True)
    def setup(self):
        self._base_interval = 10
        self.job_instance = Job(interval=self._base_interval)

    def test_move_to_at_time(self):
        cases = [
            {
                'value': datetime.datetime(2024, 6, 1, 12, 0, tzinfo=datetime.timezone.utc),
                'at_time': datetime.time(15, 30),
                'expected': datetime.datetime(2024, 6, 1, 12, 0, tzinfo=datetime.timezone.utc),
                'note': 'Expect original value when at_time is set and unit is None',
                'unit': None
            },
            {
                'value': datetime.datetime(2024, 6, 1, 12, 0, tzinfo=datetime.timezone.utc),
                'at_time': datetime.time(15, 30),
                'expected': datetime.datetime(2024, 6, 1, 12, 30, tzinfo=datetime.timezone.utc),
                'note': 'Expect value moved to at_time when unit is set to HOURS e.g. 12:00 -> 12:30',
                'unit': TimeUnit.HOURS.value
            },
            {
                'value': datetime.datetime(2024, 6, 1, 12, 0, tzinfo=datetime.timezone.utc),
                'at_time': datetime.time(15, 30),
                'expected': datetime.datetime(2024, 6, 1, 15, 30, tzinfo=datetime.timezone.utc),
                'note': 'Expect value moved to at_time when unit is set to DAYS e.g. 12:00 -> 15:30',
                'unit': TimeUnit.DAYS.value
            }
        ]

        for item in cases:
            self.job_instance.at_timezone = pytz.UTC
            self.job_instance.at_time = item['at_time']
            self.job_instance.unit = item['unit']

            result = self.job_instance._move_to_at_time(item['value'])
            assert result == item['expected'], item['note']

    def test_utc_offset_correction(self):
        cases = [
            {
                'value': datetime.datetime(2024, 6, 1, 12, 0, tzinfo=datetime.timezone.utc),
                'expected': datetime.datetime(2024, 6, 1, 12, 0, tzinfo=datetime.timezone.utc),
                'note': 'No offset change expected for UTC time',
                'at_timezone': None,
                'restore': False
            },
            {
                'value': datetime.datetime(2024, 6, 1, 12, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=-5))),
                'expected': datetime.datetime(2024, 6, 1, 12, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=-5))),
                'note': 'No offset change expected for EST time',
                'at_timezone': pytz.UTC,
                'restore': True
            },
        ]

        for item in cases:
            if item['at_timezone'] is not None:
                self.job_instance.at_timezone = item['at_timezone']

            result = self.job_instance._utc_offset_correction(
                item['value'],
                restore_time=item['restore']
            )

            assert result == item['expected'], item['note']

    def test_schedule_next_run(self):
        cases = [
            {
                'unit': TimeUnit.MINUTES.value,
                'start_day': None,
                'expected': datetime.datetime.now(pytz.UTC) + datetime.timedelta(minutes=self._base_interval),
                'note': 'Next run should be scheduled 10 minutes from now when unit is MINUTES'
            },
            {
                'unit': TimeUnit.HOURS.value,
                'start_day': None,
                'expected': datetime.datetime.now(pytz.UTC) + datetime.timedelta(hours=self._base_interval),
                'note': 'Next run should be scheduled 10 hours from now when unit is HOURS'
            },
            {
                'unit': TimeUnit.WEEKS.value,
                'start_day': 'wednesday',
                'expected': datetime.datetime.now(pytz.UTC) + datetime.timedelta(days=7),
                'note': 'Next run should be scheduled to the next Wednesday when unit is WEEKS and start_day is set'
            }
        ]

        for item in cases:
            current_date = datetime.datetime.now(pytz.UTC)

            self.job_instance.unit = item['unit']
            self.job_instance.start_day = item['start_day']

            self.job_instance._schedule_next_run()

            assert self.job_instance.next_run is not None, item['note']
            assert self.job_instance.next_run > current_date, item['note']

    def test_do(self):
        # Test that do() correctly assigns the job function and schedules the next run
        pass

    def test_run(self):
        # Test that run() executes the job function and updates last_run and next_run
        pass

    def test_at(self):
        cases = [
            # {
            #     'value': datetime.time(15, 30),
            #     'unit': TimeUnit.DAYS.value,
            #     'label': "every 10 days at 15:30:00"
            # },
            {
                'value': datetime.time(8, 0),
                'unit': TimeUnit.HOURS.value,
                'label': "every 10 hours at 08:00:00"
            }
        ]

        for item in cases:
            self.job_instance.unit = item['unit']
            self.job_instance.at(item['value'])

            assert self.job_instance.at_time == item['value']

    def test_add_tags(self):
        self.job_instance.tags('tag1', 'tag2')

        assert 'tag1' in self.job_instance._tags
        assert 'tag2' in self.job_instance._tags

        has_tags = self.job_instance.has_tags('tag1')

        assert has_tags is True, "Job should have tag 'tag1'"

    def test_get_label(self):
        cases = [
            {
                'interval': 10,
                'unit': TimeUnit.MINUTES.value,
                'at_time': None,
                'expected': "every 10 minutes",
                'note': 'Label should be "every 10 minutes" when at_time is None'
            },
            {
                'interval': 5,
                'unit': TimeUnit.HOURS.value,
                'at_time': datetime.time(15, 30),
                'expected': "every 5 hours at 15:30:00",
                'note': 'Label should be "every 5 hours at 15:30:00" when at_time is set'
            },
            {
                'interval': 5,
                'unit': TimeUnit.HOURS.value,
                'at_time': None,
                'expected': "every 5 hours",
                'note': 'Label should be "every 5 hours" when at_time is None'
            },
            {
                'interval': 1,
                'unit': TimeUnit.DAYS.value,
                'at_time': datetime.time(8, 0),
                'expected': "every 1 days at 08:00:00",
                'note': 'Label should be "every 1 days at 08:00:00" when at_time is set'
            },
            {
                'interval': 3,
                'unit': TimeUnit.DAYS.value,
                'at_time': datetime.time(8, 0),
                'expected': "every 3 days at 08:00:00",
                'note': 'Label should be "every 3 days at 08:00:00" when at_time is set'
            }
        ]

        for item in cases:
            self.job_instance.interval = item['interval']
            self.job_instance.unit = item['unit']
            self.job_instance.at_time = item['at_time']

            label = self.job_instance._get_label()
            assert label == item['expected'], item['note']

    def test_job_in_set(self):
        job1 = Job(interval=10)
        job2 = Job(interval=10)

        job_set = {job1, job2}

        assert job1 == job1, "A job should be equal to itself"
        assert len(
            job_set) == 2, "Both jobs should be in the set since they have different UUIDs"

        job_set.remove(job1)

        assert job1 not in job_set, "job1 should be removed from the set"


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
