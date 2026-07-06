import asyncio
import time
from typing import NoReturn
from simplecron.typings import TypeBaseScheduler
import threading
from simplecron.base import BaseScheduler, Job
from abc import ABC, abstractmethod
import uuid
from simplecron.context import Context  


class BackgroundThread(threading.Thread):
    def __init__(self, *schedulers: TypeBaseScheduler, scheduler_context: Context = None) -> None:
        super().__init__(daemon=True)

        self.name = f"bgt-{uuid.uuid4()}"
        self.schedulers = schedulers

        self._scheduler_context = scheduler_context or Context()
        self._scheduler_context.setdefault('main_scheduler_name', self.name)
        self._scheduler_context.setdefault('main_scheduler', self)

        self._stop_event = threading.Event()

    def run(self) -> NoReturn:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while not self._stop_event.is_set():
            for scheduler in self.schedulers:
                scheduler.run_pending(context=self._scheduler_context)

            time.sleep(1)


class BackgroundSchedulerInterface(ABC):
    @abstractmethod
    def create(self, *schedulers: TypeBaseScheduler, context: Context = None) -> BackgroundThread:
        """Start the background scheduler."""
        pass


class BackgroundScheduler(BackgroundSchedulerInterface):
    """A scheduler that runs in the background as a separate thread."""

    def create(self, *schedulers: TypeBaseScheduler, context: Context = None) -> BackgroundThread:
        context = context or Context()
        context.setdefault('main_scheduler', self)

        instance = BackgroundThread(*schedulers, scheduler_context=context)
        instance.start()
        instance.join()
        return instance


def create_background_scheduler(runner: BackgroundSchedulerInterface, *schedulers: TypeBaseScheduler, context: Context = None) -> BackgroundThread:
    """Create a background scheduler that runs in a separate thread."""
    context = context or Context()
    background_scheduler = runner.create(*schedulers, context=context)
    return background_scheduler


s = BaseScheduler()

def executor(job: "Job", **kwargs):
    print(f"Executing job: {job} with kwargs: {kwargs}")

s.create_every(5).seconds.do(executor, google='great')

instance = BackgroundScheduler()
create_background_scheduler(instance, s)
