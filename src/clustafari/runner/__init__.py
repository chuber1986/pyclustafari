"""Runner base classes."""

import abc
import logging
from collections.abc import Callable, Iterable, Mapping
from functools import partial
from itertools import repeat
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
        """Create delayed asyncronouse execution of a function and do NOT wait for the result."""
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

        nkwargs = 0
        nargs = 0

        iargs: Iterable | list = []
        ikwargs: Iterable | list = []

        if args is not None:
            iargs = list(args)
            nargs = len(iargs)
        elif kwargs is not None:
            iargs = repeat([])
            nargs = -1

        if kwargs is not None:
            ikwargs = list(kwargs)
            nkwargs = len(ikwargs)
            if nargs == -1:
                nargs = nkwargs
        elif args is not None:
            ikwargs = repeat({})
            nkwargs = nargs

        if nargs != nkwargs:
            msg = "If provided, the list of keyword arguments must have the same length as the list of argument."
            raise ValueError(msg)

        partial_fn = partial(fn, **fixed_kwargs)
        return [
            self.apply_async(partial_fn, *a, return_object=return_object, **kwa)
            for a, kwa in zip(iargs, ikwargs, strict=False)
        ]

    @abc.abstractmethod
    def _run(self, runobj: Runnable) -> RunInformation: ...
