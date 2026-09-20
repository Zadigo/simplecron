import time

from simplecron import base
from simplecron.base import Job, logger


def executor(job: Job):
    logger.info("Executor called")


base.every(15, tag="my_tag").seconds.do(executor)


if __name__ == "__main__":
    while True:
        base.run_pending()
        time.sleep(1)
