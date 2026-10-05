from simplecron.providers import JobNotificationMessage, Provider, RedisDatabase


def test_provider(mock_scheduler):
    instance = Provider(mock_scheduler)
    instance.attach(RedisDatabase())
    assert len(instance.observers) == 1


def test_notify_observers(mock_scheduler, job_fixture, current_time):
    instance = Provider(mock_scheduler)
    instance.attach(RedisDatabase())
    assert len(instance.observers) == 2

    instance.notify(
        job_fixture,
        JobNotificationMessage(job_uuid="test-uuid", runned_at=str(current_time)),
    )
