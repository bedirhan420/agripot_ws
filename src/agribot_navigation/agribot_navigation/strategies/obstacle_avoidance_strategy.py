"""
ObstacleAvoidanceStrategy - dinamik engeller (traktor/isci/hayvan) algilandiginda
MissionContext tarafindan devreye alinir.

Nav2'nin costmap + local planner (DWB/RegulatedPurePursuit) altyapisini
kullanarak anlik yorunge guncellemesi yapar (proje dokumaninin 3.1
bolumunde istenen "Nav2 uzerinde anlik yorunge guncellemeleri").
Engel gectikten sonra MissionContext otomatik olarak RowFollowingStrategy'e
geri doner (bkz. state_machine/states.py: ObstacleAvoidanceState.handle).
"""
from typing import Optional

from agribot_core.interfaces.i_navigation_strategy import INavigationStrategy
from agribot_core.common.types import Pose3D


class ObstacleAvoidanceStrategy(INavigationStrategy):

    def __init__(self, safety_margin_m: float = 0.6):
        self._safety_margin = safety_margin_m
        self._resume_pose: Optional[Pose3D] = None

    def activate(self, context) -> None:
        # Aktivasyon aninda son bilinen sira-ici hedefi sakla; engel gectikten
        # sonra RowFollowingStrategy bu civarda tekrar devreye girer.
        self._resume_pose = context.get_current_pose()
        context.enable_nav2_local_avoidance(safety_margin_m=self._safety_margin)

    def compute_command(self, context):
        # Hiz komutu Nav2 costmap+local planner tarafindan uretilir ve
        # dogrudan robota gonderilir; bu strateji sadece durum izler.
        return None

    def is_finished(self, context) -> bool:
        return context.is_path_clear_of_dynamic_obstacles()

    def get_current_goal_pose(self) -> Optional[Pose3D]:
        return self._resume_pose
