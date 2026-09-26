"""
EKF Sensor Fusion.

UYGULAMA NOTU
-------------
Production ortaminda EKF'yi sifirdan yazmak yerine ROS2 ekosistemindeki
olgunlasmis `robot_localization` paketinin `ekf_node`'unu KULLANMANIZI
oneririz: agribot_bringup/config/ekf_params.yaml dosyasi bu node icin
zaten hazirlanmistir (bkz. o dosya). Bu durumda bu dosyadaki
`LightweightEKF` sinifina hic gerek kalmaz.

Bu iskelet sinif iki durumda faydalidir:
  (a) egitim/arastirma amacli, IMU + tekerlek odometrisi + gorsel odometriyi
      ozel bir sekilde (ornegin cift oranli, sira-farkinda) birlestirmek
      istediginizde,
  (b) robot_localization'i devreye almadan once algoritmayi anlamak/
      prototiplemek icin.

Durum vektoru: [x, y, theta, v, omega]  (basit diferansiyel-surus modeli)
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class ImuSample:
    angular_velocity_z: float
    linear_acceleration_x: float
    dt: float


@dataclass
class OdomSample:
    linear_velocity_x: float
    angular_velocity_z: float


class LightweightEKF:
    """Egitim amacli, camurlu zeminde tekerlek kaymasina karsi basit bir EKF."""

    def __init__(self, wheel_slip_process_noise: float = 0.15):
        self._state = np.zeros(5)  # x, y, theta, v, omega
        self._P = np.eye(5) * 0.1
        # Camurlu/engebeli zeminde tekerlek odometrisine daha az, IMU/gorsel
        # odometriye daha fazla guvenmek icin surec gurultusu kasitli yuksek tutulur.
        self._Q = np.diag([0.01, 0.01, 0.02, wheel_slip_process_noise, 0.05])
        self._R_imu = np.diag([0.05, 0.05])
        self._R_odom = np.diag([0.1, 0.1])

    def predict(self, dt: float) -> None:
        x, y, theta, v, omega = self._state
        self._state = np.array([
            x + v * np.cos(theta) * dt,
            y + v * np.sin(theta) * dt,
            theta + omega * dt,
            v,
            omega,
        ])
        F = np.eye(5)
        F[0, 2] = -v * np.sin(theta) * dt
        F[0, 3] = np.cos(theta) * dt
        F[1, 2] = v * np.cos(theta) * dt
        F[1, 3] = np.sin(theta) * dt
        F[2, 4] = dt
        self._P = F @ self._P @ F.T + self._Q

    def update_with_imu(self, sample: ImuSample) -> None:
        z = np.array([sample.angular_velocity_z, sample.linear_acceleration_x])
        H = np.zeros((2, 5))
        H[0, 4] = 1.0  # omega
        H[1, 3] = 1.0  # v'nin turevi yaklasiklikla v olarak modellenir (basitlestirme)
        self._kalman_update(z, H, self._R_imu)

    def update_with_wheel_odom(self, sample: OdomSample, slip_confidence: float = 1.0) -> None:
        """
        slip_confidence: 0..1, RowDetector/traction-estimator tarafindan saglanan
        ve tekerlek kaymasi tespit edildiginde dusurulen bir agirlik (ornegin
        beklenen ile gerceklesen ilerleme arasindaki fark buyukse dusurulur).
        Bu, EKF'nin camurlu bolgede tekerlek odometrisine korlemesine ASIRI
        guvenmesini engeller.
        """
        z = np.array([sample.linear_velocity_x, sample.angular_velocity_z])
        H = np.zeros((2, 5))
        H[0, 3] = 1.0
        H[1, 4] = 1.0
        effective_R = self._R_odom / max(slip_confidence, 1e-3)
        self._kalman_update(z, H, effective_R)

    def _kalman_update(self, z: np.ndarray, H: np.ndarray, R: np.ndarray) -> None:
        y = z - H @ self._state
        S = H @ self._P @ H.T + R
        K = self._P @ H.T @ np.linalg.inv(S)
        self._state = self._state + K @ y
        self._P = (np.eye(5) - K @ H) @ self._P

    @property
    def state(self) -> np.ndarray:
        return self._state.copy()
