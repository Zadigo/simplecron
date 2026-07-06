import datetime
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Sequence, Union


if TYPE_CHECKING:
    from simplecron.base import BaseScheduler, Job, Cancel


type TypeJob = "Job"

type TypeJobReturn = "Cancel" | None


# | Coroutine["Job", None, None]
type TypeJobFunction[T = "Job", R = TypeJobReturn] = Callable[[T], R] | Callable[[T], Coroutine[Any, Any, R]]

type TypeBaseScheduler = "BaseScheduler"

type TypeEventListenerCallback = Callable[[Sequence["Job"]], None]

type TypeDatetimes = Union[datetime.datetime, datetime.time, datetime.timedelta]
