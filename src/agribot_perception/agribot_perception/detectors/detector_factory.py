"""
DetectorFactory - Factory Pattern.

perception_node.py, hangi detektor sinifinin ornceklendirilecegini
bilmek zorunda degildir; yalnizca ROS2 parametresinden gelen bir
string anahtar (ornegin "yolov8") verir. Yeni bir detektor eklemek
icin bu dosyayi (Open/Closed'a aykiri sekilde) degistirmek yerine
`DetectorFactory.register("yeni_model", YeniDetector)` cagrilir.
"""
from typing import Callable, Dict, Optional

from agribot_core.interfaces.i_detector import IDetector
from agribot_perception.detectors.yolov8_detector import YOLOv8Detector


class DetectorFactory:
    _registry: Dict[str, Callable[..., IDetector]] = {
        "yolov8": YOLOv8Detector,
    }

    @classmethod
    def register(cls, name: str, builder: Callable[..., IDetector]) -> None:
        cls._registry[name] = builder

    @classmethod
    def create(cls, detector_type: str, **kwargs) -> IDetector:
        if detector_type not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(f"Bilinmeyen detector_type='{detector_type}'. Mevcut: {available}")
        return cls._registry[detector_type](**kwargs)
