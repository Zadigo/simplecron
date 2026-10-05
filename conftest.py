import datetime
from unittest.mock import Mock

import pytest

from simplecron.base import BaseScheduler, Job


@pytest.fixture
def mock_scheduler(job_fixture, current_time):
    return Mock(
        spec=BaseScheduler,
        jobs=Mock(return_value=[job_fixture]),
        get_next_run=Mock(
            return_value=current_time,
        ),
    )


@pytest.fixture
def job_fixture():
    return Mock(spec=Job, job_uuid="mock_uuid", destructure=Mock(return_value={}))


@pytest.fixture
def current_time():
    return datetime.datetime.now(datetime.UTC)
