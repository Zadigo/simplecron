import time

from simplecron.base import Job, default_scheduler, logger
from simplecron.providers import RedisDatabase


def executor(job: Job):
    logger.info("Executor called")


default_scheduler.providers.attach(RedisDatabase())
default_scheduler.create_every(15, tag="my_tag").seconds.do(executor)


if __name__ == "__main__":
    while True:
        default_scheduler.run_pending()
        time.sleep(1)
