"""
NavigationManagerNode - Facade.

MissionContext + State/Strategy Pattern'lerini rclpy dunyasina baglayan
"kenar" (edge) sinif. Sorumlulugu SADECE baglama (wiring):
  - ROS2 topic/action/service'lerini dinler ve MissionContext'e
    saf-Python fonksiyonlar (closures) olarak enjekte eder,
  - sabit frekansli timer ile context.tick()'i cagirir.

Is mantigi (ne zaman hangi duruma gecilecegi) BURADA DEGIL,
state_machine/ ve strategies/ altinda yasar (Single Responsibility).
"""
import numpy as np
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist, PoseStamped
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import Odometry

from agribot_core.common.types import Pose3D
from agribot_msgs.msg import FruitDetectionArray
from agribot_navigation.state_machine.mission_context import MissionContext


class NavigationManagerNode(Node):

    def __init__(self):
        super().__init__("navigation_manager_node")

        self.declare_parameter("control_frequency_hz", 20.0)
        self.declare_parameter("home_pose_xyz", [0.0, 0.0, 0.0])
        self.declare_parameter("obstacle_proximity_threshold_m", 1.5)

        self._latest_points = np.zeros((0, 3))
        self._latest_pose = Pose3D(0.0, 0.0, 0.0)
        self._pending_targets = []
        self._obstacle_close = False
        self._nav2_client = ActionClient(self, NavigateToPose, "navigate_to_pose")

        self.create_subscription(PointCloud2, "/camera/depth/points", self._on_point_cloud, qos_profile_sensor_data)
        self.create_subscription(Odometry, "/odometry/filtered", self._on_odometry, 10)
        self.create_subscription(FruitDetectionArray, "/agribot/perception/detections", self._on_detections, 10)
        self._cmd_vel_pub = self.create_publisher(Twist, "/cmd_vel", 10)

        home_xyz = self.get_parameter("home_pose_xyz").value
        self._context = MissionContext(
            cmd_vel_publisher=self._cmd_vel_pub.publish,
            row_cloud_provider=lambda: self._latest_points,
            pose_provider=lambda: self._latest_pose,
            harvest_target_provider=self._pop_next_reachable_target,
            obstacle_detector=lambda: self._obstacle_close,
            nav2_goal_sender=self._send_nav2_goal,
            harvest_requester=self._request_harvest_action,
            home_pose=Pose3D(*home_xyz),
        )
        self._context.request_start()

        dt = 1.0 / float(self.get_parameter("control_frequency_hz").value)
        self.create_timer(dt, self._context.tick)

        self.get_logger().info("NavigationManagerNode hazir; RowFollowingState ile baslayacak.")

    def _on_point_cloud(self, msg: PointCloud2) -> None:
        points = point_cloud2.read_points_numpy(msg, field_names=("x", "y", "z"), skip_nans=True)
        self._latest_points = points

    def _on_odometry(self, msg: Odometry) -> None:
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        self._latest_pose = Pose3D(p.x, p.y, p.z, q.x, q.y, q.z, q.w, frame_id=msg.header.frame_id)

    def _on_detections(self, msg: FruitDetectionArray) -> None:
        # Sadece olgun (RIPE) ve 3D konumu olan meyveleri hasat kuyruguna al.
        RIPE = 3
        for det in msg.detections:
            if det.has_3d_pose and det.maturity_level == RIPE:
                self._pending_targets.append(det)
        # TODO(Faz 6): ayni meyvenin bir onceki karede zaten kuyrukta olup
        # olmadigini track_id ile kontrol ederek tekrar eklemeyi engelle.

        # Basit engel yakinlik kontrolu: gorus alanindaki noktalarin cok yakinda
        # yogunlasmasi -> potansiyel dinamik engel (traktor/isci). Gercek
        # implementasyonda ayri bir dinamik-nesne tespit modeli kullanilmalidir.
        threshold = float(self.get_parameter("obstacle_proximity_threshold_m").value)
        close_points = self._latest_points[self._latest_points[:, 0] < threshold] if len(self._latest_points) else []
        self._obstacle_close = len(close_points) > 200

    def _pop_next_reachable_target(self):
        if not self._pending_targets:
            return None
        return self._pending_targets.pop(0)

    def _send_nav2_goal(self, pose: Pose3D) -> None:
        goal = NavigateToPose.Goal()
        goal.pose = PoseStamped()
        goal.pose.header.frame_id = pose.frame_id
        goal.pose.pose.position.x = pose.x
        goal.pose.pose.position.y = pose.y
        goal.pose.pose.position.z = pose.z
        goal.pose.pose.orientation.x = pose.qx
        goal.pose.pose.orientation.y = pose.qy
        goal.pose.pose.orientation.z = pose.qz
        goal.pose.pose.orientation.w = pose.qw
        self._nav2_client.wait_for_server(timeout_sec=2.0)
        self._nav2_client.send_goal_async(goal)

    def _request_harvest_action(self, target, on_done) -> None:
        # ManipulationNode'a HarvestFruit action-goal gonderilir.
        # Ic detaylar: agribot_manipulation/nodes/manipulation_node.py
        # Burada sadece cagri arayuzu tanimlanmistir (TODO: ActionClient baglantisi).
        self.get_logger().info(f"Hasat istegi gonderildi: {target.track_id}")
        on_done(None)  # TODO: gercek action sonucu ile degistir


def main(args=None):
    rclpy.init(args=args)
    node = NavigationManagerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
