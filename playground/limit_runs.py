from simplecron.context import Context
from src.simplecron import base
from src.simplecron.base import Job, logger


def executor(job: Job, context: Context | None = None, **kwargs):
    logger.info(f"Executor called with context: {context.json_data}")


job = base.every(10).seconds.do(executor)
job.with_limited_runs(5)

if __name__ == "__main__":
    base.start_blocking()
