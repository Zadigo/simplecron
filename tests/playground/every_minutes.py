import time
import datetime
from simplecron import base


def some_func(job: base.Job, *args, **kwargs):
    print("Hello, World!", job)


base.every(30).minutes.at(datetime.time(0, 0)).do(some_func)

while True:
    base.run_pending()
    time.sleep(1)
