from simplecron import base
from simplecron.base import Job, logger


def executor(job: Job):
    logger.info("Executor called")


base.every(15).seconds.do(executor)

if __name__ == "__main__":
    base.start_blocking()
