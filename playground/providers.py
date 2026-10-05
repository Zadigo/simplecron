import time

from simplecron import base
from simplecron.base import Job, logger
from simplecron.providers import RedisDatabase


def executor(job: Job, **kwargs):
    logger.warning("Executor called")


base.default_scheduler.providers.attach(RedisDatabase())

base.every(10).seconds.do(executor)
base.every(60).seconds.do(executor)

if __name__ == "__main__":
    while True:
        base.run_pending()
        time.sleep(1)
