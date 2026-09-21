import datetime
from typing import TYPE_CHECKING, Awaitable, Callable, Sequence, Union

if TYPE_CHECKING:
    from src.simplecron.base import BaseScheduler, Cancel, Job


type TypeJob = "Job"

type TypeJobReturn = "Cancel" | None

type TypeJobFunction[T = "Job", R = TypeJobReturn] = Callable[[T], R]

type TypeAsyncJobFunction[T = "Job", R = TypeJobReturn] = Callable[[T], Awaitable[R]]

type TypeBaseScheduler = "BaseScheduler"

type TypeEventListenerCallback = Callable[[Sequence["Job"]], None]

type TypeDatetimes = Union[datetime.datetime, datetime.time, datetime.timedelta]
