import time

from src.simplecron import base
from src.simplecron.base import Job, logger
from src.simplecron.providers import RedisDatabase


def executor(job: Job):
    logger.warning("Executor called")


base.default_scheduler.providers.attach(RedisDatabase())
base.every(15).seconds.do(executor)
base.every(30).seconds.do(executor)

if __name__ == "__main__":
    while True:
        base.run_pending()
        time.sleep(1)
