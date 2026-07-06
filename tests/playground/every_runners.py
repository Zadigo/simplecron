from simplecron.runners import Schedulers
from simplecron.base import BaseScheduler, Job
from simplecron.utils import TimeUnit


s = Schedulers()

s1 = BaseScheduler()
s2 = BaseScheduler()


def executor(job: Job):
    print(f"Executing job: {job}")


s.add(s1, unit=TimeUnit.SECONDS, interval=10, job_func=executor)
s.add(s2, unit=TimeUnit.SECONDS, interval=15, job_func=executor)

if __name__ == "__main__":
    try:
        s.start_blocking()
    except KeyboardInterrupt:
        print("Exiting...")
