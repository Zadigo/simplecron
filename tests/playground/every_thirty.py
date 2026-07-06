import datetime
import time

import pytz
from simplecron import base
from simplecron.base import Cancel


def executor(job: base.Job):
    print("* Last:", str(job.last_run), "Next:", str(job.next_run))


async def exucutor_async(job: base.Job):
    print("* Last:", str(job.last_run), "Next:", str(job.next_run))
    return Cancel(job, reason="Test cancel")


base.every(1).minutes.at(
    datetime.time(second=10),
    timezone=pytz.UTC
).do(exucutor_async)


if __name__ == "__main__":
    try:
        while True:
            base.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
