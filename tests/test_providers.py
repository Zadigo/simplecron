import datetime
from unittest.mock import Mock

import pytest

from src.simplecron.base import BaseScheduler, Job
from src.simplecron.providers import JobNotificationMessage, Provider, RedisDatabase


@pytest.fixture
def mock_job():
    return Mock(spec=Job, job_uuid="mock_uuid", destructure=Mock(return_value={}))


@pytest.fixture
def mock_scheduler(mock_job):
    return Mock(
        spec=BaseScheduler,
        jobs=Mock(return_value=[mock_job]),
        get_next_run=Mock(
            return_value=datetime.datetime.now(),
        ),
    )


def test_provider(mock_scheduler):
    instance = Provider(mock_scheduler)
    instance.attach(RedisDatabase())
    assert len(instance.observers) == 1


def test_notify_observers(mock_scheduler, mock_job):
    instance = Provider(mock_scheduler)
    instance.attach(RedisDatabase())
    assert len(instance.observers) == 1
    instance.notify(
        mock_job, JobNotificationMessage(runned_at=str(datetime.datetime.now()))
    )
