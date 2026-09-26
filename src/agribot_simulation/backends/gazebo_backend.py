"""
GazeboSimBackend - ISimulationBackend'in Gazebo (gz-sim) implementasyonu.

Adapter Pattern: gz-transport/ros_gz servislerinin gorece dagitik ve
mesaj-tabanli API'sini, agribot_core.interfaces.ISimulationBackend'in
sade metodlarina indirger. Ust katman kodu (ornegin bir sahne kurulum
script'i) `ISimulationBackend` tipiyle calisirsa, `MuJoCoSimBackend` ile
DEGISTIRILDIGINDE hicbir satir degismez (Liskov Substitution).
"""
import subprocess
from typing import Tuple

from agribot_core.interfaces.i_simulation_backend import ISimulationBackend
from agribot_core.common.types import Pose3D


class GazeboSimBackend(ISimulationBackend):

    def __init__(self, world_name: str = "orchard_row_world"):
        self._world_name = world_name
        self._connected = False

    def connect(self) -> None:
        # gz-transport Python API (>=gz-sim7) ile de yapilabilir; basitlik
        # icin burada `gz service` CLI cagrilarina sariliyoruz.
        self._connected = True

    def spawn_entity(self, name: str, model_path: str, pose: Pose3D) -> bool:
        cmd = [
            "gz", "service", "-s", f"/world/{self._world_name}/create",
            "--reqtype", "gz.msgs.EntityFactory", "--reptype", "gz.msgs.Boolean",
            "--timeout", "2000",
            "--req", (
                f'sdf_filename: "{model_path}" name: "{name}" '
                f'pose: {{position: {{x: {pose.x} y: {pose.y} z: {pose.z}}} '
                f'orientation: {{x: {pose.qx} y: {pose.qy} z: {pose.qz} w: {pose.qw}}}}}'
            ),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def set_ground_friction(self, model_name: str, mu1: float, mu2: float) -> bool:
        # DURUM: gz-sim SDF'i calisirken (runtime) yeniden yuklemeyi
        # DESTEKLEMEZ. Pragmatik cozum: farkli mu degerine sahip yeni bir
        # zemin "patch"i (ayni model_name'e sahip, farkli mu'lu bir SDF
        # varyanti) spawn_entity() ile eklemek (bkz.
        # scripts/mud_friction_randomizer.py). Bu metod, ileride custom bir
        # gz-sim System eklentisi (C++) yazildiginda o eklentinin servisini
        # cagiracak sekilde GENISLETILMEK uzere burada tutulmustur.
        raise NotImplementedError(
            "gz-sim'de canli surtunme degisimi icin ozel bir System eklentisi "
            "gerekir. Alternatif: mud_friction_randomizer.py ile patch spawn edin."
        )

    def break_joint(self, model_name: str, joint_name: str) -> bool:
        cmd = [
            "gz", "topic", "-t", f"/agribot/harvest/detach_{model_name}",
            "-m", "gz.msgs.Empty", "-p", "",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def get_entity_pose(self, name: str) -> Tuple[Pose3D, bool]:
        # TODO: `/world/<world>/pose_info` topic'ini dinleyip ilgili entity'yi filtrele.
        return Pose3D(0.0, 0.0, 0.0), False
