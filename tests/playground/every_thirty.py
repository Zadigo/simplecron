import datetime
from email.policy import strict
import time

import pytz
from simplecron import base


def executor(job: base.Job):
    print("Hello, World!", str(job.last_run), str(job.next_run))


base.every(1).minutes.at(
    datetime.time(second=30),
    timezone=pytz.UTC
).do(executor)


if __name__ == "__main__":
    while True:
        base.run_pending()
        time.sleep(1)
