"""
MuJoCoSimBackend - ISimulationBackend'in mujoco_ros koprusu uzerinden
MuJoCo implementasyonu (Adapter Pattern).

MuJoCo'nun kontak dinamiklerinin camur/tekerlek etkilesiminde daha
kararli sonuc verdigi durumlarda (proje dokumaninin 4. bolumunde
belirtildigi gibi) bu backend tercih edilebilir.

ONEMLI: mujoco_ros koprusunun VARSAYILAN ROS2 arayuzu, `eq_active`
(equality constraint aktiflik) degerini disaridan degistirmeye izin
vermez; "kirilabilir eklem" (breakable joint) ozelligi icin
mujoco_ros'a kucuk bir servis eklentisi (`/set_equality_active`) EKLEMEK
GEREKIR (bkz. docs/ARCHITECTURE.md, "MuJoCo backend notlari"). Bu sinif
o servisin var oldugunu varsayar; servis eklenene kadar break_joint()
NotImplementedError firlatir.
"""
from typing import Tuple

from agribot_core.interfaces.i_simulation_backend import ISimulationBackend
from agribot_core.common.types import Pose3D


class MuJoCoSimBackend(ISimulationBackend):

    def __init__(self, node=None):
        """
        Args:
            node: rclpy Node -- servis/topic cagirilari icin kullanilir.
                  Bu sinif rclpy'a DOGRUDAN bagimli degildir; node disaridan
                  enjekte edilir (Dependency Injection).
        """
        self._node = node

    def connect(self) -> None:
        # mujoco_ros koprusunun ayakta oldugunu dogrulamak icin
        # ilgili servis/topic'lerin varligini kontrol edebilirsiniz.
        pass

    def spawn_entity(self, name: str, model_path: str, pose: Pose3D) -> bool:
        # MuJoCo'da runtime spawn, XML sahnenin yeniden derlenmesini (mj_loadXML)
        # gerektirir; bu genelde SIMULASYON BASLANGICINDA (sahne kurulurken)
        # yapilir, Gazebo'daki gibi calisirken serbestce degildir.
        raise NotImplementedError(
            "MuJoCo'da runtime entity spawn desteklenmiyor; agribot_scene.xml "
            "icine sahne kurulum asamasinda ekleyin."
        )

    def set_ground_friction(self, model_name: str, mu1: float, mu2: float) -> bool:
        # MuJoCo'da <geom friction="mu1 mu2_torsional mu3_rolling"/> alani
        # mj_model.geom_friction uzerinden RUNTIME'DA degistirilebilir --
        # bu, Gazebo backend'ine gore buyuk bir avantajdir. Gercek
        # implementasyon mujoco_ros'un ilgili servisini cagirmalidir.
        # TODO: self._node uzerinden /mujoco/set_geom_friction servisini cagir.
        return False

    def break_joint(self, model_name: str, joint_name: str) -> bool:
        # TODO: /mujoco/set_equality_active servisi (custom eklenti) cagrilir:
        #   request.equality_name = joint_name; request.active = False
        raise NotImplementedError(
            "mujoco_ros'a '/mujoco/set_equality_active' servisini eklemeniz gerekiyor "
            "(bkz. docs/ARCHITECTURE.md)."
        )

    def get_entity_pose(self, name: str) -> Tuple[Pose3D, bool]:
        return Pose3D(0.0, 0.0, 0.0), False
