import datetime
import time

from simplecron import base
from simplecron.base import Job, logger


def executor(job: Job):
    logger.info("Executor called")


delta = datetime.timedelta(minutes=2)
base.every(30, tag="my_tag").until(limit=delta).seconds.do(executor)


if __name__ == "__main__":
    while True:
        base.run_pending()
        time.sleep(1)
