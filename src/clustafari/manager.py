"""Main module."""

import logging
from collections.abc import Callable, Iterable, Mapping
from typing import Any

from clustafari.config import NodeConfig
from clustafari.runner import Runnable

__all__ = ["ClusterContext"]


logger = logging.getLogger(__name__)


class ClusterContext:
    """PyClustafari context manager."""

    def __init__(self, config: NodeConfig) -> None:
        """Initialize ClusterContext with configuration."""
        self._config = config
        self._runs: list[Runnable] = []

    def __enter__(self) -> "ClusterContext":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        """Exit context manager."""
        for runnable in self._runs:
            del runnable

    def apply(self, fn: Callable, /, *args: Any, return_object: bool = False, **kwargs: Any) -> Any:
        """Create delayed execution of a function and wait for the result."""
        logger.debug("Manage call 'apply'")
        return self._config.runner.apply(fn, *args, return_object=return_object, **kwargs)

    def apply_async(self, fn: Callable, /, *args: Any, return_object: bool = False, **kwargs: Any) -> Runnable:
        """Create delayed asyncronouse execution of a function and do NOT wait for the result."""
        logger.debug("Manage call 'apply_async'")
        return self._config.runner.apply_async(fn, *args, return_object=return_object, **kwargs)

    def map(
        self,
        fn: Callable,
        args: Iterable[Iterable] | None = None,
        kwargs: Iterable[Mapping] | None = None,
        return_object: bool = False,  # noqa: FBT001, FBT002
        **fixed_kwargs: Any,
    ) -> list[Any]:
        """Apply function to a list of arguments and wait for the results."""
        logger.debug("Manage call 'map'")
        return self._config.runner.map(fn, args, kwargs, return_object=return_object, **fixed_kwargs)

    def map_async(
        self,
        fn: Callable,
        args: Iterable[Iterable] | None = None,
        kwargs: Iterable[Mapping] | None = None,
        return_object: bool = False,  # noqa: FBT001, FBT002
        **fixed_kwargs: Any,
    ) -> list[Runnable]:
        """Apply function to a list of arguments and do NOT wait for the results."""
        logger.debug("Manage call 'map_async'")
        return self._config.runner.map_async(fn, args, kwargs, return_object=return_object, **fixed_kwargs)
