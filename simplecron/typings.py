from typing import TYPE_CHECKING, Callable, Coroutine, Sequence


if TYPE_CHECKING:
    from simplecron.base import BaseScheduler, Job, Cancel


type TypeJob = "Job"

type TypeJobReturn = Cancel | None


# | Coroutine["Job", None, None]
type TypeJobFunction = Callable[["Job"], TypeJobReturn]

type TypeBaseScheduler = "BaseScheduler"

type TypeEventListenerCallback = Callable[[Sequence["Job"]], None]
