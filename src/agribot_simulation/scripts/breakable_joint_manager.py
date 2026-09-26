#!/usr/bin/env python3
"""
BreakableJointManager.

agribot_manipulation'daki ForceController hedef kopma kuvvetine
ulastiginda (ya da ManipulationNode bunu ONAYLADIGINDA), bu node
ilgili apple_fruit modelinin DetachableJoint eklentisine "detach"
sinyali gonderir (bkz. models/apple_fruit/model.sdf <detach_topic>).

Bu node, ManipulationNode'dan GELEN bir servis cagrisiyla tetiklenir;
boylece "ne zaman koparilacagina" ManipulationNode (is mantigi) karar
verir, bu node yalnizca simulasyon-ozel detay olan "nasil koparilacagini"
bilir (Single Responsibility + katmanlar arasi ayrisma).
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import Empty

from agribot_msgs.srv import PlanHarvest  # ornek; gercek projede ozel bir
                                            # DetachFruit.srv tanimlanmasi onerilir


class BreakableJointManagerNode(Node):

    def __init__(self):
        super().__init__("breakable_joint_manager")
        self._detach_publishers = {}
        # ManipulationNode, hasat basarili oldugunda bu servisi cagirir.
        self.create_service(PlanHarvest, "/agribot/harvest/detach_fruit", self._on_detach_request)

    def _get_or_create_publisher(self, fruit_model_name: str):
        if fruit_model_name not in self._detach_publishers:
            topic = f"/agribot/harvest/detach_{fruit_model_name}"
            self._detach_publishers[fruit_model_name] = self.create_publisher(Empty, topic, 1)
        return self._detach_publishers[fruit_model_name]

    def _on_detach_request(self, request, response):
        fruit_model_name = request.target.track_id  # spawn sirasinda track_id modele isim olarak verilmis olmali
        publisher = self._get_or_create_publisher(fruit_model_name)
        publisher.publish(Empty())
        self.get_logger().info(f"Kirilabilir eklem tetiklendi: {fruit_model_name}")
        response.plan_found = True
        return response


def main(args=None):
    rclpy.init(args=args)
    node = BreakableJointManagerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
