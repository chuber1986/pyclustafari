"""Runner base classes."""

import abc
import logging
from collections.abc import Callable, Iterable, Mapping
from functools import partial
from typing import Any

from .info import RunInformation
from .runnable import Runnable

logger = logging.getLogger(__name__)


class BaseRunner(abc.ABC):
    """Base class for cluster specific Runners."""

    def apply(self, fn: Callable, /, *args: Any, return_object: bool = False, **kwargs: Any) -> Any:
        """Create delayed execution of a function and wait for the result."""
        logger.debug("Call 'apply'")
        return self.apply_async(fn, *args, return_object=return_object, **kwargs).get(blocking=True)

    def apply_async(self, fn: Callable, /, *args: Any, return_object: bool = False, **kwargs: Any) -> Runnable:
        """Create delayed asynchronous execution of a function and do NOT wait for the result."""
        logger.debug("Call 'apply_async'")
        runobj = Runnable(
            fn,
            *args,
            return_object=return_object,
            **kwargs,
        )

        logger.info("Execute '%s' with %s", repr(runobj), self.__class__.__name__)
        self._run(runobj)
        return runobj

    def map(
        self,
        fn: Callable,
        args: Iterable[Iterable] | None = None,
        kwargs: Iterable[Mapping] | None = None,
        return_object: bool = False,  # noqa: FBT001, FBT002
        **fixed_kwargs: Any,
    ) -> list[Any]:
        """Apply function to a list of arguments and wait for the results."""
        logger.debug("Call 'map'")
        runners = self.map_async(fn, args, kwargs, return_object=return_object, **fixed_kwargs)
        return [runner.get(blocking=True) for runner in runners]

    def map_async(
        self,
        fn: Callable,
        args: Iterable[Iterable] | None = None,
        kwargs: Iterable[Mapping] | None = None,
        return_object: bool = False,  # noqa: FBT001, FBT002
        **fixed_kwargs: Any,
    ) -> list[Runnable]:
        """Apply function to a list of arguments and do NOT wait for the results."""
        logger.debug("Call 'map_async'")

        iargs = list(args) if args is not None else []
        ikwargs = list(kwargs) if kwargs is not None else []

        if args is not None and kwargs is not None and len(iargs) != len(ikwargs):
            msg = "If provided, the list of keyword arguments must have the same length as the list of argument."
            raise ValueError(msg)

        n = max(len(iargs), len(ikwargs))
        partial_fn = partial(fn, **fixed_kwargs)
        runners: list[Runnable] = []
        for i in range(n):
            a = iargs[i] if iargs else ()
            kwa = ikwargs[i] if ikwargs else {}
            runners.append(self.apply_async(partial_fn, *a, return_object=return_object, **kwa))
        return runners

    @abc.abstractmethod
    def _run(self, runobj: Runnable) -> RunInformation: ...
