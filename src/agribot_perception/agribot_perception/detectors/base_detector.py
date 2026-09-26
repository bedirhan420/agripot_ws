"""
BaseDetector - IDetector icin ortak iskelet (opsiyonel).

Somut detektorler (YOLOv8Detector) her seyi sifirdan yazmak yerine bu
sinifi genisleterek yalnizca model-ozel kismi (_run_inference) implemente
eder. Bu bir hafif Template Method kullanimidir: detect() akisi (giris
dogrulama -> cikarim -> post-processing) sabittir, _run_inference degisir.
"""
from abc import abstractmethod
from typing import List, Optional

import numpy as np

from agribot_core.interfaces.i_detector import IDetector
from agribot_core.common.types import DetectionResult


class BaseDetector(IDetector):

    def __init__(self) -> None:
        self._loaded = False

    def detect(self, rgb_image: np.ndarray, depth_image: Optional[np.ndarray] = None) -> List[DetectionResult]:
        if not self._loaded:
            raise RuntimeError("Detektor kullanilmadan once load_model() cagrilmalidir.")
        if rgb_image is None or rgb_image.size == 0:
            return []
        return self._run_inference(rgb_image, depth_image)

    @abstractmethod
    def _run_inference(self, rgb_image: np.ndarray, depth_image: Optional[np.ndarray]) -> List[DetectionResult]:
        raise NotImplementedError
