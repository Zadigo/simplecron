import time

from simplecron import base
from simplecron.base import Job, logger


def executor(job: Job):
    logger.info(f"Executor called with context: {job.get_base_context.json_data}")


def before_callback(job: Job):
    logger.info("Before callback called")


def after_callback(job: Job):
    logger.info("After callback called")


base.every(10).seconds.do(executor)

if __name__ == "__main__":
    while True:
        base.run_pending(context={"example_key": "example_value"})
        time.sleep(1)
