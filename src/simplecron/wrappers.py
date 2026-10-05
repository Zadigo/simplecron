from collections.abc import Sequence
from typing import Any

from simplecron.typings import TypeBaseScheduler, TypeJobFunction, TypeJobReturn


class _FunctionChain:
    """Chains multiple job functions together, passing the
    result of one as the input to the next.

    .. code-block:: python

        def func1(job, **kwargs):
            ...

        def func2(job, **kwargs):
            ...

        every(5).seconds.do(FunctionChain([func1, func2]))
    """

    def __init__(self, funcs: Sequence[TypeJobFunction]):
        self.funcs = funcs
        self._scheduler: TypeBaseScheduler | None = None

    def __call__(self, *args, **kwargs) -> TypeJobReturn:
        self._scheduler = kwargs.get("scheduler")

        if self._scheduler is None:
            raise ValueError("Scheduler must be provided in kwargs")

        result: Any | None = None
        for func in self.funcs:
            if result is not None:
                result = func(*args, result=result, **kwargs)
            else:
                result = func(*args, **kwargs)
        return result
