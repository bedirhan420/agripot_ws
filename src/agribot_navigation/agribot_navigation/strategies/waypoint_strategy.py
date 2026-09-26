"""
WaypointStrategy - sira donuslerinde veya GPS'in kismen guvenilir oldugu
acik alanlarda (sıralar arasi manevra) kullanilan Nav2 tabanli strateji.

Not: Proje dokumani GPS'in HER ZAMAN guvenilir olmadigini vurguluyor;
bu yuzden bu strateji yalnizca sira-disi (satir sonu donusleri gibi)
kisa, dusuk riskli manevralarda ve EKF guven skoru yeterince yuksekken
tercih edilir (secim mantigi: NavigationManagerNode / MissionContext).
"""
from typing import Optional

from agribot_core.interfaces.i_navigation_strategy import INavigationStrategy
from agribot_core.common.types import Pose3D


class WaypointStrategy(INavigationStrategy):

    def __init__(self):
        self._goal_pose: Optional[Pose3D] = None
        self._nav2_client = None  # NavigationManagerNode tarafindan enjekte edilir

    def set_goal(self, goal_pose: Pose3D) -> None:
        self._goal_pose = goal_pose

    def activate(self, context) -> None:
        if self._goal_pose is None:
            raise RuntimeError("WaypointStrategy aktive edilmeden once set_goal() cagrilmalidir.")
        context.send_nav2_goal(self._goal_pose)

    def compute_command(self, context):
        # Asil hareket komutunu Nav2'nin kendi controller_server'i uretir;
        # bu strateji yalnizca hedefi verir ve tamamlanmasini bekler (bkz. is_finished).
        return None

    def is_finished(self, context) -> bool:
        return context.is_nav2_goal_reached()

    def get_current_goal_pose(self) -> Optional[Pose3D]:
        return self._goal_pose
