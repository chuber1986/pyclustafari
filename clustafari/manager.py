"""Main module."""

import logging
from collections.abc import Iterable, Mapping
from typing import Any, Callable

from clustafari.config import NodeConfig
from clustafari.runner import Runnable

__all__ = ["ClusterContext"]


class ClusterContext:
    """PyClustafari context manager."""

    def __init__(self, config: NodeConfig):
        self._config = config
        self._runs: list[Runnable] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for runnable in self._runs:
            del runnable

    def apply(
        self, fn: Callable, /, *args, return_object: bool = False, **kwargs
    ) -> Any:
        logging.debug("Manage call 'apply'")
        return self._config.runner.apply(
            fn, *args, return_object=return_object, **kwargs
        )

    def apply_async(
        self, fn: Callable, /, *args, return_object: bool = False, **kwargs
    ) -> Runnable:
        logging.debug("Manage call 'apply_async'")
        return self._config.runner.apply_async(
            fn, *args, return_object=return_object, **kwargs
        )

    def map(
        self,
        fn: Callable,
        args: Iterable[Iterable] | None = None,
        kwargs: Iterable[Mapping] | None = None,
        return_object: bool = False,
        **fixed_kwargs,
    ) -> list[Any]:
        logging.debug("Manage call 'map'")
        return self._config.runner.map(
            fn, args, kwargs, return_object=return_object, **fixed_kwargs
        )

    def map_async(
        self,
        fn: Callable,
        args: Iterable[Iterable] | None = None,
        kwargs: Iterable[Mapping] | None = None,
        return_object: bool = False,
        **fixed_kwargs,
    ) -> list[Runnable]:
        logging.debug("Manage call 'map_async'")
        return self._config.runner.map_async(
            fn, args, kwargs, return_object=return_object, **fixed_kwargs
        )
