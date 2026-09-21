import datetime
import time

import pytz

from src.simplecron import base
from src.simplecron.base import Job, logger


def executor(job: Job):
    logger.info("Executor called")


delta = datetime.datetime.now(tz=pytz.timezone("Europe/Paris")) + datetime.timedelta(
    minutes=2
)
base.every(5).days.at(delta.time()).do(executor)


if __name__ == "__main__":
    while True:
        base.run_pending()
        time.sleep(1)
