"""
IRobotState - State Pattern arayuzu.

Her somut durum (IdleState, RowFollowingState, ...) kendi giris/cikis
davranisini ve "bu dongude ne yapilmali" mantigini kapsuller. Boylece
MissionContext icinde dev bir if/elif zinciri yerine, her durum kendi
sinifinda yasar (Single Responsibility + Open/Closed: yeni bir durum
eklemek icin mevcut durumlar degistirilmez).
"""
from abc import ABC, abstractmethod


class IRobotState(ABC):

    @abstractmethod
    def on_enter(self, context: "agribot_navigation.state_machine.mission_context.MissionContext") -> None:
        """Duruma girerken bir kerelik kurulum (ilgili navigasyon stratejisini aktive etmek gibi)."""
        raise NotImplementedError

    @abstractmethod
    def handle(self, context) -> None:
        """Kontrol dongusunun her adiminda cagrilir; gerekirse context.transition_to(...) tetikler."""
        raise NotImplementedError

    @abstractmethod
    def on_exit(self, context) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError
