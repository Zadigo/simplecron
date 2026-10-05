from simplecron import base
from simplecron.base import Job, logger


def executor(job: Job, **kwargs):
    logger.info(f"Executor called with context: {job.get_base_context.json_data}")


job = base.every(10).seconds.do(executor)
job.with_limited_runs(5)

if __name__ == "__main__":
    base.start_blocking()
