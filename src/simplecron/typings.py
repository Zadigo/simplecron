import datetime
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Protocol, Sequence, Union

if TYPE_CHECKING:
    from src.simplecron.base import BaseScheduler, Cancel, Job
    from src.simplecron.context import Context


type TypeJob = "Job"

type TypeJobReturn = Cancel | None

# type TypeJobFunction[T = "Job", R = TypeJobReturn] = Callable[[T], R]

type TypeAsyncJobFunction[T = "Job", R = TypeJobReturn] = Callable[[T], Awaitable[R]]

type TypeBaseScheduler = "BaseScheduler"

type TypeEventListenerCallback = Callable[[Sequence["Job"]], None]

type TypeDatetimes = Union[datetime.datetime, datetime.time, datetime.timedelta]


class JobFunction[T: Job, R: TypeJobReturn](Protocol):
    def __call__(self, job: T, context: Context | None = None, **kwargs: Any) -> R: ...


type TypeJobFunction[T: Job, R: TypeJobReturn] = JobFunction[T, R]
