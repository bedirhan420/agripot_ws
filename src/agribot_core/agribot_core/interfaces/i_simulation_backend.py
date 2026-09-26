"""
ISimulationBackend - Adapter Pattern.

Proje hem Gazebo (Ignition) hem de mujoco_ros koprusu uzerinden MuJoCo
kullanabilecek sekilde tasarlanmali (bkz. proje dokumani, bolum 4).
Ust katmanlar (agribot_simulation/scripts/*) hangi fizik motorunun
calistigini bilmemeli; bu arayuz farkli backend API'lerini ortak bir
sozlesme altinda gizler.

Somut implementasyonlar: agribot_simulation/backends/gazebo_backend.py
                         agribot_simulation/backends/mujoco_backend.py
"""
from abc import ABC, abstractmethod
from typing import Tuple

from agribot_core.common.types import Pose3D


class ISimulationBackend(ABC):

    @abstractmethod
    def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def spawn_entity(self, name: str, model_path: str, pose: Pose3D) -> bool:
        raise NotImplementedError

    @abstractmethod
    def set_ground_friction(self, model_name: str, mu1: float, mu2: float) -> bool:
        """Camur etkisini simule etmek icin zemin surtunme katsayilarini ayarlar."""
        raise NotImplementedError

    @abstractmethod
    def break_joint(self, model_name: str, joint_name: str) -> bool:
        """
        'Kirilabilir eklem' mekanizmasini tetikler.
        Gazebo'da: DetachableJoint sistem eklentisinin detach topic'ine yayin yapar.
        MuJoCo'da: ilgili equality constraint'i (weld) mj_data.eq_active=0 yaparak devre disi birakir.
        """
        raise NotImplementedError

    @abstractmethod
    def get_entity_pose(self, name: str) -> Tuple[Pose3D, bool]:
        """(pose, basarili_mi) dondurur."""
        raise NotImplementedError
