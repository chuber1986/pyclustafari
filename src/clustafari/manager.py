"""Main module."""

import logging
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

from clustafari.config import NodeConfig
from clustafari.runner import Runnable

__all__ = ["ClusterContext"]


logger = logging.getLogger(__name__)


class ClusterContext:
    """PyClustafari context manager."""

    def __init__(self, config: NodeConfig, artifacts_dir: Path | str | None = None) -> None:
        """Initialize ClusterContext with configuration.

        Args:
            config: The backend configuration to dispatch with.
            artifacts_dir: Explicit artifacts root for all runs dispatched
                through this context, overriding the
                ``CLUSTAFARI_ARTIFACT_DIR`` environment variable and the
                ``~/.clustafari`` default.

        """
        self._config = config
        self._artifacts_dir = artifacts_dir

    def __enter__(self) -> "ClusterContext":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        """Exit context manager. Async runs keep living on."""

    def apply(self, fn: Callable, /, *args: Any, return_object: bool = False, **kwargs: Any) -> Any:
        """Create delayed execution of a function and wait for the result."""
        logger.debug("Manage call 'apply'")
        return self._config.runner.apply(
            fn, *args, return_object=return_object, artifacts_dir=self._artifacts_dir, **kwargs
        )

    def apply_async(self, fn: Callable, /, *args: Any, return_object: bool = False, **kwargs: Any) -> Runnable:
        """Create delayed asynchronous execution of a function and do NOT wait for the result."""
        logger.debug("Manage call 'apply_async'")
        return self._config.runner.apply_async(
            fn, *args, return_object=return_object, artifacts_dir=self._artifacts_dir, **kwargs
        )

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
        return self._config.runner.map(
            fn, args, kwargs, return_object=return_object, **self._map_root_kwargs(), **fixed_kwargs
        )

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
        return self._config.runner.map_async(
            fn, args, kwargs, return_object=return_object, **self._map_root_kwargs(), **fixed_kwargs
        )

    def _map_root_kwargs(self) -> dict[str, Any]:
        """Return the artifacts-dir keyword for map dispatches, if any."""
        if self._artifacts_dir is not None:
            return {"artifacts_dir": self._artifacts_dir}
        return {}
