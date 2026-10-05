import time

import pytz

from simplecron import base
from simplecron.base import Job, logger


def executor(job: Job):
    logger.info("Executor called")


timezone = pytz.timezone("Europe/Paris")
base.every(1).hour.with_timezone(timezone).with_limited_runs(1).do(executor)

if __name__ == "__main__":
    while True:
        base.run_pending()
        time.sleep(1)
