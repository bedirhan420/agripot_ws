"""
ForceController - uc-islevci (end-effector) icin kapali-cevrim kuvvet kontrolu.

Proje gereksinimi 3.3: "meyveyi zedelemeden tutabilmesi ve dalindan
koparmak icin gereken ideal Newton kuvvetini uygulamasi."

Basit bir PI kuvvet kontrolcusu: hedef kuvvete ulasana, maksimum
kuvveti asana (meyve hasar riski) ya da zaman asimina ugrayana kadar
calisir. Gercek robotta bu donguyu ya dogrudan bir F/T sensor
donanim-dongusunde (ornegin 500 Hz) ya da ros2_control bir
"effort_controller" uzerinden calistirmak gerekir; bu sinif algoritmayi
donanimdan bagimsiz (saf Python) tutar.
"""
import time
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class ForceControlResult:
    achieved_force_n: float
    exceeded_max: bool
    timed_out: bool


class ForceController:

    def __init__(
        self,
        read_force_n: Callable[[], float],
        apply_effort: Callable[[float], None],
        kp: float = 0.6,
        ki: float = 0.05,
        control_rate_hz: float = 100.0,
        timeout_sec: float = 3.0,
    ):
        """
        Args:
            read_force_n: F/T sensorunden anlik kuvveti (N) okuyan fonksiyon.
            apply_effort: gripper/kol eklemine efor (Nm ya da N, donanima bagli) uygulayan fonksiyon.
        """
        self._read_force = read_force_n
        self._apply_effort = apply_effort
        self._kp = kp
        self._ki = ki
        self._dt = 1.0 / control_rate_hz
        self._timeout = timeout_sec

    def apply_target_force(self, target_force_n: float, max_force_n: float, tolerance_n: float = 0.3) -> ForceControlResult:
        integral_error = 0.0
        start_time = time.monotonic()

        while True:
            elapsed = time.monotonic() - start_time
            if elapsed > self._timeout:
                return ForceControlResult(self._read_force(), exceeded_max=False, timed_out=True)

            measured = self._read_force()
            if measured >= max_force_n:
                self._apply_effort(0.0)
                return ForceControlResult(measured, exceeded_max=True, timed_out=False)

            error = target_force_n - measured
            if abs(error) <= tolerance_n:
                return ForceControlResult(measured, exceeded_max=False, timed_out=False)

            integral_error += error * self._dt
            effort = self._kp * error + self._ki * integral_error
            self._apply_effort(effort)

            time.sleep(self._dt)
