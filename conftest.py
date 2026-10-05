import datetime

import pytest


@pytest.fixture
def current_time():
    return datetime.datetime.now(datetime.UTC)
