"""
PerceptionNode - rclpy Node (Facade + Subject/Observer).

Sorumluluklari (Single Responsibility ile SINIRLI tutulmustur):
  1) senkronize RGB-D goruntu al,
  2) DetectorFactory ile olusturulan IDetector'a cikarim yaptir,
  3) MaturityClassifier ile olgunluk ata,
  4) sonucu agribot_msgs/FruitDetectionArray olarak yayinla,
  5) ic Subject araciligiyla surec-ici gozlemcileri (varsa) bilgilendir.

"Nasil tespit edilir" (YOLOv8 detayi) ve "nasil olgunluk atanir" bilgisi
BU SINIFTA DEGIL, enjekte edilen IDetector / IMaturityClassifier
implementasyonlarinda yasar (Dependency Inversion).
"""
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from message_filters import ApproximateTimeSynchronizer, Subscriber
from cv_bridge import CvBridge
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import PoseStamped

from agribot_core.interfaces.observer import Subject
from agribot_perception.detectors.detector_factory import DetectorFactory
from agribot_perception.maturity.maturity_classifier import HsvThresholdMaturityClassifier
from agribot_perception.utils.image_utils import crop_bbox

from agribot_msgs.msg import FruitDetection, FruitDetectionArray


class PerceptionNode(Node, Subject):

    def __init__(self):
        Node.__init__(self, "perception_node")
        Subject.__init__(self)

        self.declare_parameter("detector_type", "yolov8")
        self.declare_parameter("weights_path", "/opt/agribot/models/apple_yolov8.pt")
        self.declare_parameter("device", "cuda:0")
        self.declare_parameter("confidence_threshold", 0.5)
        self.declare_parameter("rgb_topic", "/camera/color/image_raw")
        self.declare_parameter("depth_topic", "/camera/depth/image_rect_raw")
        self.declare_parameter("camera_info_topic", "/camera/color/camera_info")

        detector_type = self.get_parameter("detector_type").value
        weights_path = self.get_parameter("weights_path").value
        device = self.get_parameter("device").value

        # --- Dependency Injection: Factory somut sinifi gizler ---
        self._detector = DetectorFactory.create(
            detector_type,
            confidence_threshold=self.get_parameter("confidence_threshold").value,
        )
        self._detector.load_model(weights_path, device=device)
        self._detector.warmup()
        self.get_logger().info(f"Detektor yuklendi: {detector_type} ({weights_path})")

        self._maturity_classifier = HsvThresholdMaturityClassifier()
        self._bridge = CvBridge()

        self._detections_pub = self.create_publisher(FruitDetectionArray, "/agribot/perception/detections", 10)

        rgb_sub = Subscriber(self, Image, self.get_parameter("rgb_topic").value, qos_profile=qos_profile_sensor_data)
        depth_sub = Subscriber(self, Image, self.get_parameter("depth_topic").value, qos_profile=qos_profile_sensor_data)
        self._sync = ApproximateTimeSynchronizer([rgb_sub, depth_sub], queue_size=5, slop=0.05)
        self._sync.registerCallback(self._on_synced_images)

        self.create_subscription(CameraInfo, self.get_parameter("camera_info_topic").value, self._on_camera_info, 10)

    def _on_camera_info(self, msg: CameraInfo) -> None:
        # K = [fx 0 cx; 0 fy cy; 0 0 1]
        if hasattr(self._detector, "set_camera_intrinsics"):
            self._detector.set_camera_intrinsics(fx=msg.k[0], fy=msg.k[4], cx=msg.k[2], cy=msg.k[5])

    def _on_synced_images(self, rgb_msg: Image, depth_msg: Image) -> None:
        rgb = self._bridge.imgmsg_to_cv2(rgb_msg, desired_encoding="bgr8")
        depth = self._bridge.imgmsg_to_cv2(depth_msg, desired_encoding="passthrough")

        detections = self._detector.detect(rgb, depth)

        array_msg = FruitDetectionArray()
        array_msg.header = rgb_msg.header

        for i, det in enumerate(detections):
            crop = crop_bbox(rgb, det.bbox.x_min, det.bbox.y_min, det.bbox.x_max, det.bbox.y_max)
            maturity, _confidence = self._maturity_classifier.classify(crop)

            msg = FruitDetection()
            msg.header = rgb_msg.header
            msg.track_id = f"{rgb_msg.header.stamp.sec}_{i}"
            msg.fruit_type = det.class_name
            msg.maturity_level = self._maturity_to_uint8(maturity)
            msg.confidence = det.confidence
            msg.bbox_x_min, msg.bbox_y_min = det.bbox.x_min, det.bbox.y_min
            msg.bbox_x_max, msg.bbox_y_max = det.bbox.x_max, det.bbox.y_max

            if det.position_3d is not None:
                pose = PoseStamped()
                pose.header = rgb_msg.header
                pose.pose.position.x = det.position_3d.x
                pose.pose.position.y = det.position_3d.y
                pose.pose.position.z = det.position_3d.z
                msg.pose_3d = pose
                msg.has_3d_pose = True
            else:
                msg.has_3d_pose = False

            array_msg.detections.append(msg)

        self._detections_pub.publish(array_msg)
        # Surec-ici gozlemciler (ornegin bir DetectionLogger) icin:
        self.notify("detections_published", array_msg)

    @staticmethod
    def _maturity_to_uint8(maturity) -> int:
        from agribot_core.common.types import MaturityLevel
        mapping = {
            MaturityLevel.UNKNOWN: 0, MaturityLevel.UNRIPE: 1,
            MaturityLevel.RIPENING: 2, MaturityLevel.RIPE: 3, MaturityLevel.OVERRIPE: 4,
        }
        return mapping.get(maturity, 0)


def main(args=None):
    rclpy.init(args=args)
    node = PerceptionNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
