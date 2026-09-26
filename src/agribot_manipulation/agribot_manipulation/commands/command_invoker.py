"""
CommandInvoker - Command Pattern'in "invoker" bileseni.

Hasat komutlarini FIFO kuyrukta tutar, calistirir, basarisiz kavrama
(FAILED_GRASP) durumunda sinirli sayida yeniden dener, tum gecmisi
(history) loglama/telemetri icin saklar.
"""
from collections import deque
from typing import Callable, Deque, List, Optional

from agribot_core.common.types import HarvestResult
from agribot_core.interfaces.i_harvest_command import IHarvestCommand


class CommandInvoker:

    def __init__(self, max_retries: int = 2, on_command_done: Optional[Callable[[IHarvestCommand], None]] = None):
        self._queue: Deque[IHarvestCommand] = deque()
        self._history: List[IHarvestCommand] = []
        self._max_retries = max_retries
        self._on_command_done = on_command_done

    def enqueue(self, command: IHarvestCommand) -> None:
        self._queue.append(command)

    def has_pending(self) -> bool:
        return len(self._queue) > 0

    def run_next(self) -> Optional[HarvestResult]:
        if not self._queue:
            return None

        command = self._queue.popleft()
        attempts = 0
        result = command.execute()

        while result == HarvestResult.FAILED_GRASP and attempts < self._max_retries:
            attempts += 1
            result = command.execute()

        self._history.append(command)
        if self._on_command_done:
            self._on_command_done(command)
        return result

    @property
    def history(self) -> List[IHarvestCommand]:
        return list(self._history)
