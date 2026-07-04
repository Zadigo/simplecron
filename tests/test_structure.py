import time

from simplecron.base import every, run_pending
from simplecron.utils import TimeUnit


def test_every_function():
    job = every(1).seconds.do(lambda: print("Hello, World!"))
    assert job.interval == 1
    assert job.unit == TimeUnit.SECONDS.value
    assert callable(job._job_func)


def test_do_function(magenta):
    every(1).seconds.do(lambda j: magenta("Hello, World!"))

    counter = 0
    while counter < 5:
        run_pending()
        counter += 1
        time.sleep(1)
