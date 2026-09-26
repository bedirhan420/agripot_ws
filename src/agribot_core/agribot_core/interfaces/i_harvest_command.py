"""
IHarvestCommand - Command Pattern.

Her hasat girisimini bir nesneye (komuta) donusturerek:
  - CommandInvoker uzerinden kuyruklama / yeniden deneme (retry) / loglama,
  - basarisiz girisimlerde undo() ile kolun guvenli pozisyona geri cekilmesi,
saglanir. Bu, ManipulationNode'un "nasil hasat edilir" bilgisinden
izole kalmasini saglar (Single Responsibility).
"""
from abc import ABC, abstractmethod

from agribot_core.common.types import HarvestResult


class IHarvestCommand(ABC):

    @abstractmethod
    def execute(self) -> HarvestResult:
        raise NotImplementedError

    @abstractmethod
    def undo(self) -> None:
        """Basarisizlik/iptal durumunda kolu guvenli (home) pozisyona ceker."""
        raise NotImplementedError

    @abstractmethod
    def describe(self) -> str:
        """Loglama/telemetri icin insan-okunabilir aciklama."""
        raise NotImplementedError
