import time
import functools
from simplecron import base
import asyncio


def some_func(job: base.Job, *args, **kwargs):
    print("Hello, World!", job)


base.every(1).second.do(some_func)

base.default_scheduler.with_event_listener(
    base.EventListener.BEFORE,
    lambda x: print("Before job", x)
)

while True:
    base.run_pending_jobs()
    time.sleep(1)
