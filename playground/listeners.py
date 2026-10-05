import time

from simplecron.base import Job, default_scheduler, logger


def executor(job: Job):
    logger.info("Executor called")


def before_callback(job: Job):
    logger.info("Before callback called")


def after_callback(job: Job):
    logger.info("After callback called")


default_scheduler.every(15).seconds.do(executor)
default_scheduler.before_events([before_callback])
default_scheduler.after_events([after_callback])

if __name__ == "__main__":
    while True:
        default_scheduler.run_pending()
        time.sleep(1)
