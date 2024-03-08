"""Main module."""
from functools import partial
from itertools import repeat
from typing import Callable, Iterable, List, Mapping

from slurmlib.runnable import Runnable
from slurmlib.config import NodeConfig

__all__ = ["SlurmLib"]


class SlurmLib:
    """SlurmLib class."""

    def __init__(self, config: NodeConfig):
        self._config = config
        self._runs: List[Runnable] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def apply(self, fn: Callable, /, *args, **kwargs) -> Runnable:
        return self.apply_async(fn, *args, **kwargs).get(blocking=True)

    def apply_async(self, fn: Callable, /, *args, **kwargs) -> Runnable:
        self._runs.append(Runnable(fn, *args, **kwargs))
        self._runs[-1].execute()
        return self._runs[-1]

    def map(self, fn: Callable, /,
            args: Iterable | None = None,
            kwargs: Iterable[Mapping] | None = None,
            *fixed_args,
            **fixed_kwargs) -> List[Runnable]:
        runners = self.map_async(fn, args, kwargs, *fixed_args, **fixed_kwargs)
        return [runner.get(blocking=True) for runner in runners]

    def map_async(self, fn: Callable, /,
                  args: Iterable | None = None,
                  kwargs: Iterable[Mapping] | None = None,
                  *fixed_args,
                  **fixed_kwargs) -> List[Runnable]:

        nargs = -1

        if args is not None:
            iargs = list(args)
            nargs = len(iargs)
        elif kwargs is not None:
            iargs = repeat([])
        else:
            iargs = []
            nargs = 0

        if kwargs is not None:
            ikwargs = list(kwargs)
            nkwargs = len(ikwargs)
            if nargs == -1:
                nargs = nkwargs
        elif args is not None:
            ikwargs = repeat({})
            nkwargs = nargs
        else:
            ikwargs = []
            nkwargs = 0

        if nargs != nkwargs:
            raise ValueError(
                "If provided, the list of keyword arguments must have the same length as the list of argument."
            )

        partial_fn = partial(fn, *fixed_args, **fixed_kwargs)
        runs = [self.apply_async(partial_fn, *a, **kwa) for a, kwa in zip(iargs, ikwargs)]

        self._runs += runs
        return runs


def main():
    import time

    def long_running_function(paramA, paramB, *, paramC, paramD=None):
        print(paramA, paramB)
        time.sleep(10)
        print(paramC, paramD)
        return "Some return value."

    from joblib import delayed
    ddd = delayed(long_running_function)(10, 20, paramC=30, paramD=40)
    print(ddd)



    with SlurmLib(NodeConfig()) as ctx:
        runs = ctx.map(long_running_function, [[1], [2], [3]], [dict(paramC=1), dict(paramC=2), dict(paramC=3)], 20,
                       paramC=30, paramD=40)

    print(runs)


if __name__ == '__main__':
    main()
