import time

from simplecron.base import Job, default_scheduler, logger


def executor(job: Job):
    logger.info("Executor called")


default_scheduler.with_memory("some-value")
default_scheduler.with_context()
default_scheduler.create_every(30, tag="my_tag").seconds.do(executor)


if __name__ == "__main__":
    while True:
        default_scheduler.run_pending()
        time.sleep(1)
