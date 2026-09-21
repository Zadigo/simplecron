import time

from simplecron import base
from simplecron.base import Job, logger
from simplecron.providers import RedisDatabase


def executor(job: Job):
    logger.info("Executor called")


base.default_scheduler.providers.attach(RedisDatabase())
base.every(2).seconds.do(executor)

if __name__ == "__main__":
    while True:
        base.run_pending()
        time.sleep(1)
