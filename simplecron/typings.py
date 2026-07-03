from typing import TYPE_CHECKING, Callable, Coroutine


if TYPE_CHECKING:
    from simplecron.base import BaseScheduler, Job


type TypeJob = "Job"

# | Coroutine["Job", None, None]
type TypeJobFunction = Callable[["Job"], None]

type TypeBaseScheduler = "BaseScheduler"
