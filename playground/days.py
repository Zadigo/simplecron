import time

from simplecron import base
from simplecron.base import Job, logger


def executor(job: Job):
    logger.info("Executor called")


def before_callback(job: Job):
    logger.info("Before callback called")


def after_callback(job: Job):
    logger.info("After callback called")


base.every(1).thursday.do(executor)

if __name__ == "__main__":
    while True:
        base.run_pending()
        time.sleep(1)
