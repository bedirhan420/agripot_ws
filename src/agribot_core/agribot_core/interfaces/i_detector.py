"""
IDetector - algilama stratejileri icin soyut arayuz.

Interface Segregation Principle (ISP): arayuz yalnizca algilama
sorumlulugunu tasir; egitim, veri toplama vb. baska sorumluluklar
buraya karisilmaz.

Liskov Substitution Principle (LSP): bu arayuzu implemente eden
YOLOv8Detector, ileride eklenebilecek bir YOLOv9/segmentasyon
detektoru ile DetectorFactory uzerinden hicbir cagiran kodu
degistirmeden yer degistirebilir (bkz. detectors/detector_factory.py).
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from agribot_core.common.types import DetectionResult


class IDetector(ABC):
    """Strategy Pattern: tum nesne tespit stratejilerinin sozlesmesi."""

    @abstractmethod
    def load_model(self, weights_path: str, device: str = "cuda:0") -> None:
        """Model agirliklarini yukler. Node baslatilirken bir kez cagrilir."""
        raise NotImplementedError

    @abstractmethod
    def detect(self, rgb_image, depth_image: Optional[object] = None) -> List[DetectionResult]:
        """
        RGB (ve varsa derinlik) goruntusu uzerinde cikarim yapar.

        Args:
            rgb_image: HxWx3 numpy array (BGR ya da RGB, implementasyona bagli).
            depth_image: HxW numpy array (metre cinsinden derinlik), opsiyonel.

        Returns:
            List[DetectionResult]
        """
        raise NotImplementedError

    @abstractmethod
    def warmup(self) -> None:
        """Ilk cikarimdaki gecikmeyi onlemek icin modeli 'isitir' (dummy forward pass)."""
        raise NotImplementedError
