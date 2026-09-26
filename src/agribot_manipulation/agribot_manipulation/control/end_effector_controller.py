"""
EndEffectorController - gripper acma/kapama ve kavrama kuvveti komutlari.

Gercek donanimda genelde bir GripperCommand action sunucusuna (ros2_control
gripper_action_controller) baglanir; bu iskelet o baglantiyi soyutlar.
"""
from typing import Callable


class EndEffectorController:

    def __init__(self, send_gripper_command: Callable[[float, float], bool]):
        """
        Args:
            send_gripper_command: (position, max_effort) -> basarili_mi
                (ros2_control GripperCommand action client'i tarafindan saglanir)
        """
        self._send_gripper_command = send_gripper_command
        self._OPEN_POSITION = 0.04   # metre, gripper'a gore kalibre edilmeli
        self._CLOSED_POSITION = 0.0

    def open(self) -> bool:
        return self._send_gripper_command(self._OPEN_POSITION, 10.0)

    def close_with_grip_force(self, grip_force_n: float) -> bool:
        return self._send_gripper_command(self._CLOSED_POSITION, grip_force_n)
