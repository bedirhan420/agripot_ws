"""
INavigationStrategy - Strategy Pattern.

navigation_manager_node, aktif stratejiyi bu arayuz uzerinden cagirir;
hangi somut stratejinin (row following / waypoint / obstacle avoidance)
calistigini bilmek zorunda degildir (Open/Closed + Dependency Inversion).
Strateji degisimi calisirken bile (runtime) MissionContext.transition_to
ile State Pattern uzerinden tetiklenir.
"""
from abc import ABC, abstractmethod
from typing import Optional

from agribot_core.common.types import Pose3D


class INavigationStrategy(ABC):

    @abstractmethod
    def activate(self, context: "object") -> None:
        """Strateji aktif hale gelirken bir kerelik kurulum (ic durum sifirlama)."""
        raise NotImplementedError

    @abstractmethod
    def compute_command(self, context: "object"):
        """
        Tek bir kontrol dongusu adiminda calisir.

        Returns:
            geometry_msgs.msg.Twist uyumlu bir komut nesnesi (somut siniflar
            rclpy tipini import eder; bu arayuz rclpy'a bagimli DEGILDIR).
        """
        raise NotImplementedError

    @abstractmethod
    def is_finished(self, context: "object") -> bool:
        """Bu stratejinin hedefine ulasip ulasmadigini bildirir."""
        raise NotImplementedError

    @abstractmethod
    def get_current_goal_pose(self) -> Optional[Pose3D]:
        raise NotImplementedError
