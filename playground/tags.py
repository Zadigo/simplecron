import time

from simplecron.base import Job, default_scheduler, logger
from simplecron.utils import EventListenerEnum


def executor(job: Job):
    logger.info("Executor called")


def event_before(job: Job):
    print("Before job:", job._tags)


default_scheduler.create_every(10, tag="my_tag").seconds.do(executor)
default_scheduler.create_every(15, tag="other_tag").seconds.do(executor)

default_scheduler.with_event_listener(
    EventListenerEnum.BEFORE, event_before, for_tags=["my_tag"]
)


if __name__ == "__main__":
    while True:
        default_scheduler.run_pending()
        time.sleep(1)
