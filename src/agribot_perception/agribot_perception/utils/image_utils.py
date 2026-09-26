"""Kucuk, bagimsiz test edilebilir goruntu yardimci fonksiyonlari."""
import numpy as np


def crop_bbox(image: np.ndarray, x_min: float, y_min: float, x_max: float, y_max: float) -> np.ndarray:
    h, w = image.shape[:2]
    xi_min = max(0, int(x_min))
    yi_min = max(0, int(y_min))
    xi_max = min(w, int(x_max))
    yi_max = min(h, int(y_max))
    if xi_max <= xi_min or yi_max <= yi_min:
        return np.zeros((0, 0, 3), dtype=image.dtype)
    return image[yi_min:yi_max, xi_min:xi_max]


def ros_image_to_numpy(msg) -> np.ndarray:
    """sensor_msgs/Image -> numpy array. Basitlik icin cv_bridge kullanimi onerilir:

        from cv_bridge import CvBridge
        bridge = CvBridge()
        cv_image = bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

    Bu fonksiyon, cv_bridge'in mevcut olmadigi (ornegin unit test) ortamlar
    icin minimal bir yedek (fallback) saglar; encoding='rgb8'/'bgr8' varsayar.
    """
    dtype = np.uint8
    channels = 3
    return np.frombuffer(msg.data, dtype=dtype).reshape(msg.height, msg.width, channels)
