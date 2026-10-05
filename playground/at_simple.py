import datetime
import time

import pytz

from simplecron import base
from simplecron.base import Job, logger


def executor(job: Job):
    logger.info("Executor called")


timezone = pytz.timezone("Europe/Paris")
delta = datetime.datetime.now(tz=timezone) + datetime.timedelta(minutes=2)

base.every(5).days.at(delta.time()).do(executor)


if __name__ == "__main__":
    while True:
        base.run_pending()
        time.sleep(1)
