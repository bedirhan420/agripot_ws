"""
YOLOv8Detector - IDetector/BaseDetector'in somut (concrete) implementasyonu.

Bagimlilik: `pip install ultralytics --break-system-packages`

Derinlik goruntusu verildiginde, kutunun merkez pikselindeki derinlik ve
onceden kalibre edilmis kamera intrinsikleri (fx, fy, cx, cy) kullanilarak
3D konum hesaplanir (basit pinhole-kamera geri izdusumu).
"""
from typing import List, Optional

import numpy as np

from agribot_perception.detectors.base_detector import BaseDetector
from agribot_core.common.types import BoundingBox2D, DetectionResult, Pose3D


class YOLOv8Detector(BaseDetector):

    def __init__(self, camera_intrinsics: Optional[dict] = None, confidence_threshold: float = 0.5):
        super().__init__()
        self._model = None
        self._class_names: dict = {}
        self._confidence_threshold = confidence_threshold
        # fx, fy, cx, cy -- perception_node tarafindan CameraInfo topic'inden enjekte edilir
        self._intrinsics = camera_intrinsics or {"fx": 615.0, "fy": 615.0, "cx": 320.0, "cy": 240.0}

    def load_model(self, weights_path: str, device: str = "cuda:0") -> None:
        # Gec import: ultralytics agir bir bagimlilik, yalnizca gercekten
        # gerektiginde (bu metod cagrildiginda) yuklenir.
        from ultralytics import YOLO

        self._model = YOLO(weights_path)
        self._model.to(device)
        self._class_names = self._model.names
        self._loaded = True

    def warmup(self) -> None:
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        self._model.predict(dummy, verbose=False)

    def set_camera_intrinsics(self, fx: float, fy: float, cx: float, cy: float) -> None:
        self._intrinsics = {"fx": fx, "fy": fy, "cx": cx, "cy": cy}

    def _run_inference(self, rgb_image: np.ndarray, depth_image: Optional[np.ndarray]) -> List[DetectionResult]:
        results = self._model.predict(
            rgb_image, verbose=False, conf=self._confidence_threshold
        )[0]

        detections: List[DetectionResult] = []
        for box in results.boxes:
            x_min, y_min, x_max, y_max = [float(v) for v in box.xyxy[0].tolist()]
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = self._class_names.get(class_id, f"class_{class_id}")

            position_3d = None
            if depth_image is not None:
                position_3d = self._backproject_to_3d(x_min, y_min, x_max, y_max, depth_image)

            detections.append(
                DetectionResult(
                    class_id=class_id,
                    class_name=class_name,
                    confidence=confidence,
                    bbox=BoundingBox2D(x_min, y_min, x_max, y_max),
                    position_3d=position_3d,
                )
            )
        return detections

    def _backproject_to_3d(self, x_min, y_min, x_max, y_max, depth_image: np.ndarray) -> Optional[Pose3D]:
        """Kutunun merkez pikselinden basit pinhole geri izdusumu ile 3D konum tahmini."""
        cx_px = int((x_min + x_max) / 2.0)
        cy_px = int((y_min + y_max) / 2.0)

        h, w = depth_image.shape[:2]
        if not (0 <= cx_px < w and 0 <= cy_px < h):
            return None

        # TODO: tek piksel yerine kutu icindeki medyan derinligi kullanmak
        # gurultuye karsi daha dayanikli olur (ozellikle yaprak/dal karisikliginda).
        depth_m = float(depth_image[cy_px, cx_px])
        if depth_m <= 0.0 or np.isnan(depth_m):
            return None

        fx, fy = self._intrinsics["fx"], self._intrinsics["fy"]
        cam_cx, cam_cy = self._intrinsics["cx"], self._intrinsics["cy"]

        x = (cx_px - cam_cx) * depth_m / fx
        y = (cy_px - cam_cy) * depth_m / fy
        z = depth_m

        return Pose3D(x=x, y=y, z=z, frame_id="camera_optical_frame")
