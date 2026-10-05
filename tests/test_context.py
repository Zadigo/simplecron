import time

import pytest

from simplecron.base import BaseScheduler
from simplecron.context import Context
from simplecron.utils import EventListenerEnum


def test_set_and_get_value():
    context = Context()
    context.set_value("next_page", 1)

    assert context.get_value("next_page") == 1
    assert context.get_value("non_existent_key") is None


@pytest.mark.integration
def test_context_in_loop():
    s = BaseScheduler()
    s.create_every(1).seconds.do(lambda job: None)

    for i in range(5):
        s.run_pending()
        s.base_context.increment_value("runs")
        assert s.base_context.get_value("runs") == i + 1


@pytest.mark.integration
def test_context_in_loop_with_listeners():
    s = BaseScheduler()

    s.create_every(1).seconds.do(lambda job: None)

    s.with_context(Context(json_data={"runs": 0}))
    s.with_event_listener(
        EventListenerEnum.AFTER,
        lambda job: job.get_base_context.increment_value("runs"),
    )

    for i in range(3):
        s.run_pending()
        time.sleep(1)

    assert s.base_context.get_value("runs") == 2
