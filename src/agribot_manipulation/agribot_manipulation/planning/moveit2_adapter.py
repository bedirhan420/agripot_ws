"""
MoveIt2Adapter - Adapter/Facade Pattern.

MoveIt2'nin (MoveItPy / move_group action arayuzu) genis API'sini,
HarvestPlanner'in ihtiyac duydugu 4 basit metoda indirger:
plan_to_pose, execute_last_plan, compute_ik, is_pose_reachable.

Boylece:
  - HarvestPlanner, MoveIt2'nin dahili tiplerine (RobotTrajectory,
    PlanningSceneMonitor, ...) DOGRUDAN BAGIMLI OLMAZ (DIP).
  - Ileride MoveIt2 yerine baska bir planlayici (ornegin ozel bir IK
    cozucu) kullanilmak istenirse, yalnizca bu adapter degisir.
"""
from typing import Optional

from agribot_core.common.types import Pose3D


class MoveIt2Adapter:

    def __init__(self, planning_group: str = "agribot_arm", planner_id: str = "RRTConnectkConfigDefault"):
        self._planning_group = planning_group
        self._planner_id = planner_id
        self._moveit_py = None   # lazy-init edilir (agir bagimlilik)
        self._last_plan = None

    def _ensure_initialized(self) -> None:
        if self._moveit_py is None:
            # from moveit.planning import MoveItPy
            # self._moveit_py = MoveItPy(node_name="agribot_moveit_py")
            # TODO: gercek MoveItPy baglantisi + planning_group konfigurasyonu.
            raise NotImplementedError(
                "MoveItPy baglantisi henuz kurulmadi. moveit_py paketini kurup "
                "bu metodu MoveIt2 setup assistant ciktilariniza gore doldurun."
            )

    def is_pose_reachable(self, pose: Pose3D) -> bool:
        """Hizli bir IK fizibilite kontrolu (carpisma kontrolu HARIC)."""
        self._ensure_initialized()
        # TODO: moveit_py compute_ik cagrisi
        return True

    def plan_to_pose(self, pose: Pose3D) -> bool:
        """Carpisma-farkinda (collision-aware) yorunge planlar; MoveIt2'nin
        planning scene'i (agac/dal modelleri) engel olarak kullanir."""
        self._ensure_initialized()
        # TODO: self._last_plan = self._moveit_py.plan(...)
        return True

    def execute_last_plan(self) -> bool:
        self._ensure_initialized()
        if self._last_plan is None:
            return False
        # TODO: self._moveit_py.execute(self._last_plan)
        return True

    def compute_approach_pose(self, target_pose: Pose3D, offset_m: float) -> Pose3D:
        """Meyvenin `offset_m` kadar onunde, kola dogru duran bir yaklasma pozu uretir."""
        # Basitlestirilmis: -x yonunde offset (gercekte meyve normali/kamera
        # bakis vektoru kullanilmali).
        return Pose3D(
            x=target_pose.x - offset_m, y=target_pose.y, z=target_pose.z,
            qx=target_pose.qx, qy=target_pose.qy, qz=target_pose.qz, qw=target_pose.qw,
            frame_id=target_pose.frame_id,
        )
