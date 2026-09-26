"""
Observer Pattern - proje icinde ROS2 topic'lerine ek olarak, ayni surec
(process) icindeki bilesenlerin birbirine dogrudan bagimli olmadan
haberlesmesi icin kullanilir.

Ornek: PerceptionNode her yeni FruitDetection kumesini yayinladiginda,
hem DetectionLogger hem de HarvestQueueBuilder gozlemcileri (observer)
ayni olaydan bagimsiz sekilde haberdar olur (Single Responsibility +
Open/Closed: yeni bir gozlemci eklemek icin PerceptionNode degismez).
"""
from abc import ABC, abstractmethod
from typing import Any, List


class IObserver(ABC):
    @abstractmethod
    def update(self, event_name: str, payload: Any) -> None:
        raise NotImplementedError


class Subject:
    """Gozlemlenebilir taban sinif. Miras yerine kompozisyonla da kullanilabilir."""

    def __init__(self) -> None:
        self._observers: List[IObserver] = []

    def attach(self, observer: IObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: IObserver) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, event_name: str, payload: Any) -> None:
        for observer in list(self._observers):
            observer.update(event_name, payload)
