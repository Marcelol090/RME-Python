"""Threaded Selection Worker — background selection processing.

Mirrors legacy C++ ``editor/selection_thread.cpp``.

For large maps (10 000+ tiles) the selection processing can take
noticeable time.  This module offloads the heavy computation to a
``QThread`` so the UI stays responsive.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QMutex, QObject, QThread, pyqtSignal

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import TileKey

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
#  Result data
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class SelectionResult:
    """Outcome of a threaded selection operation."""

    selected_keys: frozenset[TileKey]
    elapsed_ms: float
    cancelled: bool = False


# ---------------------------------------------------------------------------
#  Worker (runs on QThread)
# ---------------------------------------------------------------------------


class _SelectionComputation(QObject):
    """Performs the heavy selection computation on a background thread.

    Signals
    -------
    finished(SelectionResult)
        Emitted when the computation completes.
    progress(int)
        Emitted periodically with percentage 0-100.
    """

    finished = pyqtSignal(object)  # SelectionResult
    progress = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        self._cancel = False
        self._mutex = QMutex()

        # Set by caller before start:
        self.candidate_keys: frozenset[TileKey] = frozenset()
        self.filter_fn: Any = None  # Callable[[TileKey], bool] | None

    def cancel(self) -> None:
        """Request cancellation (thread-safe)."""
        self._mutex.lock()
        self._cancel = True
        self._mutex.unlock()

    def _is_cancelled(self) -> bool:
        self._mutex.lock()
        val = self._cancel
        self._mutex.unlock()
        return val

    def _build_cancelled_result(self, result_keys: set[TileKey], t0: float) -> SelectionResult:
        """Build a cancelled SelectionResult."""
        elapsed = (time.perf_counter() - t0) * 1000
        return SelectionResult(
            selected_keys=frozenset(result_keys),
            elapsed_ms=elapsed,
            cancelled=True,
        )

    def _passes_filter(self, key: TileKey) -> bool:
        """Return True if *key* passes the optional filter."""
        if self.filter_fn is None:
            return True
        try:
            return bool(self.filter_fn(key))
        except Exception:  # noqa: BLE001
            logger.debug("Filter error for key %s", key, exc_info=True)
            return False

    def run(self) -> None:
        """Execute the selection computation."""
        t0 = time.perf_counter()
        total = len(self.candidate_keys)
        result_keys: set[TileKey] = set()
        check_interval = max(1, total // 100)

        for i, key in enumerate(self.candidate_keys):
            if i % check_interval == 0:
                if self._is_cancelled():
                    self.finished.emit(self._build_cancelled_result(result_keys, t0))
                    return
                self.progress.emit(int(i / total * 100) if total else 100)

            if self._passes_filter(key):
                result_keys.add(key)

        elapsed = (time.perf_counter() - t0) * 1000
        self.progress.emit(100)
        self.finished.emit(
            SelectionResult(
                selected_keys=frozenset(result_keys),
                elapsed_ms=elapsed,
            )
        )


# ---------------------------------------------------------------------------
#  Public API
# ---------------------------------------------------------------------------


class SelectionWorker(QObject):
    """Manages a threaded selection computation.

    Usage::

        worker = SelectionWorker()
        worker.finished.connect(on_done)   # receives SelectionResult
        worker.progress.connect(on_pct)    # receives int 0-100
        worker.start(candidate_keys, filter_fn)

        # To cancel:
        worker.cancel()
    """

    finished = pyqtSignal(object)  # SelectionResult
    progress = pyqtSignal(int)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread: QThread | None = None
        self._computation: _SelectionComputation | None = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def start(
        self,
        candidate_keys: frozenset[TileKey],
        filter_fn: Any = None,
    ) -> None:
        """Start a threaded selection computation.

        Parameters
        ----------
        candidate_keys
            The set of tile keys to process.
        filter_fn
            Optional callable ``(TileKey) -> bool`` to filter candidates.
            If ``None``, all candidates are selected.
        """
        if self.is_running:
            logger.warning("SelectionWorker already running, cancelling previous")
            self.cancel()

        thread = QThread()
        comp = _SelectionComputation()
        comp.candidate_keys = candidate_keys
        comp.filter_fn = filter_fn

        comp.moveToThread(thread)
        thread.started.connect(comp.run)
        comp.finished.connect(self._on_finished)
        comp.progress.connect(self.progress)
        comp.finished.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)

        self._thread = thread
        self._computation = comp
        thread.start()

    def cancel(self) -> None:
        """Request cancellation of the running computation."""
        if self._computation is not None:
            self._computation.cancel()
        if self._thread is not None and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)

    def _on_finished(self, result: SelectionResult) -> None:
        """Handle computation completion."""
        self._thread = None
        self._computation = None
        self.finished.emit(result)
