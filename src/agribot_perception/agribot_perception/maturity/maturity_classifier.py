"""
MaturityClassifier - Strategy Pattern (IDetector'dan bagimsiz, ayri bir eksen).

Baslangic implementasyonu HSV renk histogrami tabanli basit bir esik
(threshold) sinifiydiricidir -- egitim verisi gerektirmez, hizli devreye
alinir. Ilerleyen fazda (bkz. ROADMAP Faz 5-6) egitimli kucuk bir CNN
(ornegin MobileNetV3) ile degistirilebilir; IMaturityClassifier arayuzu
sayesinde perception_node.py DEGISMEDEN yeni siniflandirici takilabilir.
"""
from abc import ABC, abstractmethod
from typing import Tuple

import numpy as np

from agribot_core.common.types import MaturityLevel


class IMaturityClassifier(ABC):
    @abstractmethod
    def classify(self, cropped_rgb: np.ndarray) -> Tuple[MaturityLevel, float]:
        """Returns (olgunluk_seviyesi, guven_skoru)."""
        raise NotImplementedError


class HsvThresholdMaturityClassifier(IMaturityClassifier):
    """
    Elma icin basit HSV oran tabanli sezgisel (heuristic) siniflandirici.

    TODO(Faz 6): Gercek bahce verisiyle esikleri (thresholds) kalibre et;
    ideal olarak bu esikler ConfigManager uzerinden YAML'dan okunmali.
    """

    # (hue_min, hue_max) araliklari -- OpenCV HSV: H in [0,179]
    _RED_RANGE = (0, 10)
    _YELLOW_RANGE = (20, 35)
    _GREEN_RANGE = (35, 85)

    def classify(self, cropped_rgb: np.ndarray) -> Tuple[MaturityLevel, float]:
        import cv2

        if cropped_rgb is None or cropped_rgb.size == 0:
            return MaturityLevel.UNKNOWN, 0.0

        hsv = cv2.cvtColor(cropped_rgb, cv2.COLOR_RGB2HSV)
        hue = hsv[:, :, 0]
        total_px = hue.size

        red_ratio = np.count_nonzero((hue >= self._RED_RANGE[0]) & (hue <= self._RED_RANGE[1])) / total_px
        yellow_ratio = np.count_nonzero((hue >= self._YELLOW_RANGE[0]) & (hue <= self._YELLOW_RANGE[1])) / total_px
        green_ratio = np.count_nonzero((hue >= self._GREEN_RANGE[0]) & (hue <= self._GREEN_RANGE[1])) / total_px

        if red_ratio > 0.55:
            return MaturityLevel.RIPE, min(1.0, red_ratio)
        if red_ratio > 0.3:
            return MaturityLevel.RIPENING, 0.6
        if yellow_ratio > 0.4:
            return MaturityLevel.RIPENING, 0.5
        if green_ratio > 0.5:
            return MaturityLevel.UNRIPE, min(1.0, green_ratio)

        return MaturityLevel.UNKNOWN, 0.2
