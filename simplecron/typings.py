from typing import TYPE_CHECKING, Callable, Coroutine


if TYPE_CHECKING:
    from simplecron.base import BaseCron, Job


# | Coroutine["Job", None, None]
type TypeJobFunction = Callable[["Job"], None]
