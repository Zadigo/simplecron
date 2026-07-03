import asyncio

from simplecron.runners import Schedulers
from simplecron.base import BaseScheduler, Job, TimeUnit

runner = Schedulers()

s1 = BaseScheduler()
s2 = BaseScheduler()


def first(job: Job):
    print("First job executed", job)


def second(job: Job):
    print("Second job executed", job)


runner.add(s1, unit=TimeUnit.SECONDS, interval=5, job_func=first)
runner.add(s2, unit=TimeUnit.SECONDS, interval=10, job_func=second)

# runner.start_blocking()


async def main():
    await runner.async_blocking()


if __name__ == "__main__":
    asyncio.run(main())
