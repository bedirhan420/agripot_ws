"""
RowDetector - RGB-D nokta bulutundan sira geometrisi cikarimi.

Proje dokumaninin vurguladigi temel yenilik burada: 2D Lidar SLAM yerine
3D Point Cloud isleme ile "duvarsiz" bahce/tarla sıralarinin algilanmasi.

Algoritma (basitlestirilmis iskelet):
  1) Zemin duzlemini kaldir (basit yukseklik esigi; ileri fazda RANSAC).
  2) Kalan noktalari (govde/yapraklar) yanal (lateral, Y) eksende
     histograma dok; iki yogun kume = sıranin sol/sag siniri.
  3) Iki kumenin orta noktasi = sira merkez cizgisi -> lateral_offset.
  4) Kumelerin ana ekseni (PCA) -> heading_error.

Bu sinif rclpy'a BAGIMLI DEGILDIR (saf numpy); ROS2 entegrasyonu
navigation_manager_node.py icinde, PointCloud2 mesajini numpy'a
cevirdikten sonra bu sinifi cagirarak yapilir (Single Responsibility).
"""
from typing import Optional

import numpy as np

from agribot_core.common.types import RowGeometry


class RowDetector:

    def __init__(self, ground_height_threshold_m: float = 0.08, max_row_half_width_m: float = 1.2):
        self._ground_height_threshold = ground_height_threshold_m
        self._max_row_half_width = max_row_half_width_m

    def compute_row_geometry(self, points_xyz: np.ndarray) -> RowGeometry:
        """
        Args:
            points_xyz: (N, 3) numpy array, kamera/govde cercevesinde [x(ileri), y(sol-sag), z(yukseklik)]

        Returns:
            RowGeometry
        """
        if points_xyz is None or len(points_xyz) < 50:
            return RowGeometry(0.0, 0.0, 0.0, valid=False)

        # 1) Basit zemin filtresi (TODO: RANSAC tabanli duzlem uydurma ile degistir)
        above_ground = points_xyz[points_xyz[:, 2] > self._ground_height_threshold]
        if len(above_ground) < 30:
            return RowGeometry(0.0, 0.0, 0.0, valid=False)

        # 2) Yalnizca gecerli koridor genisligindeki noktalari al (govde disi gurultuyu at)
        lateral = above_ground[:, 1]
        in_corridor = above_ground[np.abs(lateral) < self._max_row_half_width]
        if len(in_corridor) < 20:
            return RowGeometry(0.0, 0.0, 0.0, valid=False)

        left_cluster = in_corridor[in_corridor[:, 1] > 0]
        right_cluster = in_corridor[in_corridor[:, 1] <= 0]

        if len(left_cluster) < 5 or len(right_cluster) < 5:
            # Tek tarafli sira (bahcenin kenari) -- dusuk guvenle devam et
            confidence = 0.3
            lateral_offset = float(np.mean(in_corridor[:, 1]))
        else:
            left_center = float(np.mean(left_cluster[:, 1]))
            right_center = float(np.mean(right_cluster[:, 1]))
            lateral_offset = (left_center + right_center) / 2.0
            confidence = min(1.0, (len(left_cluster) + len(right_cluster)) / 200.0)

        heading_error = self._estimate_heading_error(in_corridor)

        return RowGeometry(
            lateral_offset_m=lateral_offset,
            heading_error_rad=heading_error,
            row_confidence=confidence,
            valid=True,
        )

    @staticmethod
    def _estimate_heading_error(points_xy_plane: np.ndarray) -> float:
        """PCA ile govde noktalarinin ana ekseni ve arac ileri ekseni (x) arasindaki aci farki."""
        xy = points_xy_plane[:, :2]
        xy_centered = xy - xy.mean(axis=0)
        cov = np.cov(xy_centered.T)
        eigvals, eigvecs = np.linalg.eigh(cov)
        principal_axis = eigvecs[:, np.argmax(eigvals)]
        # Ana eksenin x-eksenine gore acisi
        heading_error = float(np.arctan2(principal_axis[1], principal_axis[0]))
        # [-pi/2, pi/2] araligina normalize et (sira yonu simetrik)
        if heading_error > np.pi / 2:
            heading_error -= np.pi
        elif heading_error < -np.pi / 2:
            heading_error += np.pi
        return heading_error
