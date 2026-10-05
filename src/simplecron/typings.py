import asyncio
import datetime
from collections.abc import Awaitable, Callable, Sequence
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from simplecron.base import BaseScheduler, Cancel, Job
    from simplecron.context import Context


type TypeJob = "Job"

type TypeBaseScheduler = "BaseScheduler"

type TypeEventListenerCallback = Callable[[Sequence["Job"]], None]

type TypeDatetimes = datetime.datetime | datetime.time | datetime.timedelta

type TypeJobReturn = Any | Cancel | asyncio.Task[Any]

type TypeAsyncJobFunction[T = "Job", R = TypeJobReturn] = Callable[[T], Awaitable[R]]


class JobFunctionProtocol[T: Job, R: TypeJobReturn](Protocol):
    def __call__(self, job: T, context: Context | None = None, **kwargs: Any) -> R: ...


type TypeJobFunction[T: Job, R: TypeJobReturn] = JobFunctionProtocol[T, R]
