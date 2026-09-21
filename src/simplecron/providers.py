import json
import uuid
from abc import ABC, abstractmethod
from typing import Any

import pydantic
from pydantic import Field
from redis import Redis

from src.simplecron.typings import TypeBaseScheduler, TypeJob
from src.simplecron.utils import logger


class JobNotificationMessage(pydantic.BaseModel):
    job_uuid: str = Field(...)
    runned_at: str = Field(...)


class ProviderSavedData(pydantic.BaseModel):
    next_run: str = Field(...)
    number_of_jobs: int = Field(default=0)
    json_jobs: str = Field(...)
    last_sender: str = Field(...)


class BaseProvider(ABC):
    """Base class that defines the interface for provider implementations.
    A provider is responsible for managing and notifying observers about
    changes and updates that occur during the execution of scheduled tasks."""

    def __init__(self, scheduler: TypeBaseScheduler) -> None:
        self._scheduler = scheduler

    @abstractmethod
    def attach(self, observer: Observer) -> None:
        pass

    @abstractmethod
    def detach(self, observer: Observer) -> None:
        pass

    @abstractmethod
    def notify(
        self,
        job: TypeJob | None = None,
        job_message: JobNotificationMessage | None = None,
    ) -> None:
        pass


class Provider(BaseProvider):
    observers: list[Observer] = []

    def attach(self, observer: Observer) -> None:
        self.observers.append(observer)

    def detach(self, observer: Observer) -> None:
        if observer in self.observers:
            self.observers.remove(observer)

    def notify(
        self,
        job: TypeJob | None = None,
        job_message: JobNotificationMessage | None = None,
    ) -> None:
        for observer in self.observers:
            observer.update(self, job=job, job_message=job_message)

    def initialize(self) -> None:
        """Initialize the provider. This method can be used to set up any necessary resources or connections."""
        pass


class Observer(ABC):
    def __init__(self) -> None:
        self.uuid = uuid.uuid4()

    def __hash__(self) -> int:
        return hash(self.uuid)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} uuid={self.uuid}>"

    @abstractmethod
    def update(
        self,
        provider: BaseProvider,
        job: TypeJob | None = None,
        job_message: JobNotificationMessage | None = None,
    ) -> None:
        pass


class RedisDatabase(Observer):
    """Observer implementation that interacts with a Redis database. This observer
    listens for updates from the provider and stores relevant information in a
    Redis database.

    Attributes:
        conn (Redis): The Redis connection object.
        storage_key (str): The key used to store data in the Redis database.
    """

    def __init__(
        self, host: str = "localhost", port: int = 6379, **kwargs: Any
    ) -> None:
        super().__init__()
        self.conn = Redis(host=host, port=port, db=0, **kwargs)
        self.storage_key = f"simplecron:{self.uuid}"

        try:
            self.conn.ping()
        except Exception as e:
            logger.error(f"Error connecting to Redis: {e}")

    def update(
        self,
        provider: BaseProvider,
        job: TypeJob | None = None,
        job_message: JobNotificationMessage | None = None,
    ) -> None:
        if job is not None and job_message is not None:
            next_run = provider._scheduler.get_next_run()
            number_of_jobs = len(provider._scheduler.jobs())
            json_jobs = [job.destructure() for job in provider._scheduler.jobs()]

            run_details = ProviderSavedData(
                next_run=str(next_run) if bool(next_run) else "",
                number_of_jobs=number_of_jobs,
                json_jobs=json.dumps(json_jobs),
                last_sender=str(job_message.job_uuid) if bool(job_message) else "",
            )

            self.conn.hset(
                self.storage_key + ":details", mapping=run_details.model_dump()
            )
            self.conn.lpush(
                self.storage_key + ":runs", json.dumps(run_details.model_dump())
            )
            self.conn.publish(str(self.uuid), json.dumps(run_details.model_dump()))
