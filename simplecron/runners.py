import asyncio
import time
from typing import Any, NoReturn
from simplecron.typings import TypeBaseScheduler, TypeJob, TypeJobFunction
from simplecron.base import TimeUnit
import threading
from asgiref.sync import sync_to_async


class Context:
    def add(self, key: str, value: Any):
        setattr(self, key, value)

    def remove(self, key: str):
        if hasattr(self, key):
            delattr(self, key)

    def get_all(self) -> list[tuple[str, Any]]:
        clean_values = filter(lambda x: not x.startswith("__"), dir(self))
        return [(key, getattr(self, key)) for key in clean_values if not callable(getattr(self, key))]


class Schedulers:
    """A class to manage multiple schedulers and run them in a blocking manner."""

    schedulers: list[TypeBaseScheduler] = []

    def add(self, scheduler: TypeBaseScheduler, unit: TimeUnit, interval: int, job_func: TypeJobFunction, *args, **kwargs) -> TypeJob:
        new_job = scheduler.create_every(interval=interval)

        new_job.unit = unit.value
        new_job.do(job_func, *args, **kwargs)

        self.schedulers.append(scheduler)
        return new_job

    def start_blocking(self) -> NoReturn:
        def loop():
            while True:
                for scheduler in self.schedulers:
                    scheduler.run_pending()
                time.sleep(1)

        thread = threading.Thread(target=loop)
        thread.name = "RunningSchedulersThread"
        thread.daemon = True
        thread.start()
        thread.join()

    async def async_blocking(self):
        context = Context()
        context.add("instance", self)

        try:
            while True:
                async with asyncio.TaskGroup() as tg:
                    for scheduler in self.schedulers:
                        async_run_pending = sync_to_async(
                            scheduler.run_pending,
                            thread_sensitive=True
                        )
                        task = tg.create_task(async_run_pending())
                        # task.set_name(f"Scheduler-{scheduler.id}-Task")
                        # task.add_done_callback(
                        #     lambda t: print(
                        #         f"Scheduler {scheduler.id} task completed with result: {t.result()}")
                        # )
        except asyncio.CancelledError:
            print("Async blocking loop cancelled.")
        except KeyboardInterrupt:
            print("Async blocking loop interrupted by user.")
