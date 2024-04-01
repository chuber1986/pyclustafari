"""Main module."""

from collections.abc import Iterable, Mapping
from functools import partial
from itertools import repeat
from typing import Callable

from runner.slurm import SlurmRunner

from slurmlib.config import NodeConfig
from slurmlib.runnable import Runnable, Runner

__all__ = ["SlurmLib"]


class SlurmLib:
    """SlurmLib class."""

    def __init__(self, config: NodeConfig, runner: Runner | None = SlurmRunner()):
        self._runner = runner
        self._config = config
        self._runs: list[Runnable] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for runnable in self._runs:
            del runnable

    def apply(self, fn: Callable, /, *args, **kwargs) -> Runnable:
        return self.apply_async(fn, *args, **kwargs).get(blocking=True)

    def apply_async(self, fn: Callable, /, *args, **kwargs) -> Runnable:
        self._runs.append(Runnable(self._runner, fn, *args, **kwargs))
        self._runs[-1].execute()
        return self._runs[-1]

    def map(
        self,
        fn: Callable,
        *fixed_args,
        args: Iterable | None = None,
        kwargs: Iterable[Mapping] | None = None,
        **fixed_kwargs,
    ) -> list[Runnable]:
        runners = self.map_async(fn, args, kwargs, *fixed_args, **fixed_kwargs)
        return [runner.get(blocking=True) for runner in runners]

    def map_async(
        self,
        fn: Callable,
        *fixed_args,
        args: Iterable | None = None,
        kwargs: Iterable[Mapping] | None = None,
        **fixed_kwargs,
    ) -> list[Runnable]:

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
            raise ValueError(
                "If provided, the list of keyword arguments must have the same length as the list of argument."
            )

        partial_fn = partial(fn, *fixed_args, **fixed_kwargs)
        runs = [
            self.apply_async(partial_fn, *a, **kwa) for a, kwa in zip(iargs, ikwargs)
        ]

        self._runs += runs
        return runs
