#!/usr/bin/env python3
"""
MudFrictionRandomizer.

gz-sim canli surtunme (mu1/mu2) degisimini native olarak desteklemedigi
icin (bkz. backends/gazebo_backend.py docstring), pragmatik yaklasim:
tarla boyunca ONCEDEN farkli mu degerlerine sahip zemin "patch"lerini
(mud_ground_plane modelinin instance'lari) rastgele konumlarda spawn
etmektir. Bu, robotun farkli surtunme bolgelerinden gecerken EKF'nin
(agribot_navigation/localization) tekerlek kaymasini nasil toparladigini
test etmeyi saglar.
"""
import random

import rclpy
from rclpy.node import Node

from agribot_core.common.types import Pose3D
from agribot_simulation.backends.gazebo_backend import GazeboSimBackend


class MudFrictionRandomizerNode(Node):

    def __init__(self):
        super().__init__("mud_friction_randomizer")
        self.declare_parameter("num_patches", 4)
        self.declare_parameter("field_length_m", 12.0)
        self.declare_parameter("field_width_m", 3.0)

        self._backend = GazeboSimBackend()
        self._backend.connect()
        self._spawn_random_patches()

    def _spawn_random_patches(self) -> None:
        num_patches = self.get_parameter("num_patches").value
        length = self.get_parameter("field_length_m").value
        width = self.get_parameter("field_width_m").value

        for i in range(num_patches):
            pose = Pose3D(
                x=random.uniform(0.0, length),
                y=random.uniform(-width / 2.0, width / 2.0),
                z=0.002,  # zeminin hemen ustunde, z-fighting'i onlemek icin
            )
            # NOT: mud_ground_plane/model.sdf icindeki mu1/mu2=0.9 sabittir.
            # Gercek "camur" patch'i icin ayri bir model.sdf varyanti
            # (mu1=0.2, mu2=0.2) olusturup burada onu spawn edin:
            name = f"mud_patch_{i}"
            success = self._backend.spawn_entity(name, "model://mud_ground_plane_wet", pose)
            if success:
                self.get_logger().info(f"Camur bolgesi eklendi: {name} @ ({pose.x:.2f}, {pose.y:.2f})")
            else:
                self.get_logger().warn(f"Camur bolgesi eklenemedi: {name}")


def main(args=None):
    rclpy.init(args=args)
    node = MudFrictionRandomizerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
