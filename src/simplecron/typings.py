import asyncio
import datetime
from collections.abc import Awaitable, Callable, Sequence
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from simplecron.base import BaseScheduler, Cancel, Job, Skipped


type TypeJob = "Job"

type TypeBaseScheduler = "BaseScheduler"

type TypeEventListenerCallback = Callable[[Sequence["Job"]], None]

type TypeDatetimes = datetime.datetime | datetime.time | datetime.timedelta

type TypeJobReturn = Cancel | Skipped | asyncio.Task[Any]


class AsyncJobFunctionProtocol(Protocol):
    async def __call__(
        self,
        job: Job,
        *,
        stop_event: asyncio.Event | None = None,
        **kwargs: Any,
    ) -> Awaitable[TypeJobReturn]: ...


type TypeAsyncJobFunction = AsyncJobFunctionProtocol


class JobFunctionProtocol(Protocol):
    def __call__(
        self,
        job: Job,
        **kwargs: Any,
    ) -> TypeJobReturn: ...


type TypeJobFunction = JobFunctionProtocol | AsyncJobFunctionProtocol
