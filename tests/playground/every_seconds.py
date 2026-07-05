import time

import pytz
from simplecron import base, utils


def some_func(job: base.Job, *args, **kwargs):
    print("* Last:", str(job.last_run), "Next:", str(job.next_run))


def after_func(job: base.Job, *args, **kwargs):
    print("* After function executed!", "\n")


base.default_scheduler.with_event_listener(
    utils.EventListenerEnum.AFTER,
    after_func
)

job = base.every(10).seconds.do(some_func)
job.at_timezone = pytz.timezone("Europe/Paris")


if __name__ == "__main__":
    try:
        while True:
            base.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
