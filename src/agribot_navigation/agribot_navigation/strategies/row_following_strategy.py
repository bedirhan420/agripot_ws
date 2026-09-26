"""
RowFollowingStrategy - varsayilan (default) navigasyon stratejisi.

RowDetector'dan gelen RowGeometry'yi PD kontrolcusu ile Twist komutuna
cevirir. Nav2'nin genel amacli 2D-lidar-tabanli local planner'i yerine
BURADA ozel bir kontrolcu kullanilmasinin nedeni proje dokumaninda
belirtilen ana gereksinimdir: sıra ici hassas merkezlenme, RGB-D point
cloud tabanli olmalidir.

Dinamik engeller (traktor/isci/hayvan) algilandiginda, MissionContext
(State Pattern) bu stratejiden ObstacleAvoidanceStrategy'ye (Nav2 tabanli)
GECIS yapar; bu iki strateji ayni anda calismaz (bkz. state_machine/states.py).
"""
from typing import Optional

from agribot_core.interfaces.i_navigation_strategy import INavigationStrategy
from agribot_core.common.types import Pose3D
from agribot_navigation.row_following.row_detector import RowDetector


class RowFollowingStrategy(INavigationStrategy):

    def __init__(self, kp_lateral: float = 0.8, kp_heading: float = 1.2, cruise_speed_mps: float = 0.4):
        self._row_detector = RowDetector()
        self._kp_lateral = kp_lateral
        self._kp_heading = kp_heading
        self._cruise_speed = cruise_speed_mps
        self._last_row_geometry = None

    def activate(self, context) -> None:
        self._last_row_geometry = None

    def compute_command(self, context):
        from geometry_msgs.msg import Twist  # rclpy bagimliligi yalnizca burada

        points_xyz = context.get_latest_point_cloud()  # (N,3) numpy, MissionContext saglar
        row_geometry = self._row_detector.compute_row_geometry(points_xyz)
        self._last_row_geometry = row_geometry

        cmd = Twist()
        if not row_geometry.valid or row_geometry.row_confidence < 0.25:
            # Sira kaybedildi -> guvenli sekilde yavasla, dur (Faz 8'de "sira arama"
            # (row re-acquisition) davranisi eklenebilir).
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0
            return cmd

        cmd.linear.x = self._cruise_speed * row_geometry.row_confidence
        cmd.angular.z = -(
            self._kp_lateral * row_geometry.lateral_offset_m
            + self._kp_heading * row_geometry.heading_error_rad
        )
        return cmd

    def is_finished(self, context) -> bool:
        # Sira takibi, satirin sonuna (context.is_row_end_reached()) kadar surer.
        return context.is_row_end_reached()

    def get_current_goal_pose(self) -> Optional[Pose3D]:
        return None  # hedef nokta yerine surekli goreli kontrol uygular
