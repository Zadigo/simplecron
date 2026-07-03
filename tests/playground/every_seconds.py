import time
import datetime
from simplecron import base


def some_func(job: base.Job, *args, **kwargs):
    print("Hello, World!", job)


base.every(30).second.do(some_func)

base.default_scheduler.with_event_listener(
    base.EventListener.BEFORE,
    lambda x: print("Before job", x)
)

while True:
    base.run_pending()
    time.sleep(1)
