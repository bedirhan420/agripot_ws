"""
agribot_core.common.types
==========================
Katmanlar arasi paylasilan, framework'ten bagimsiz veri tipleri.

Bunlari ROS2 mesajlarindan (agribot_msgs) BILINCLI olarak ayri tutuyoruz:
is mantigi (planning, control, detection) saf Python dataclass'lari
uzerinden calisir; ROS2 mesaj (de)serilestirmesi yalnizca `nodes/` altindaki
"kenar" (edge) siniflarda yapilir. Boylece:
  - Is mantigi siniflari rclpy olmadan da unit test edilebilir.
  - ROS2 mesaj semasi degisse bile ic mantik etkilenmez (Dependency Inversion).
"""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Tuple


class MaturityLevel(Enum):
    UNKNOWN = auto()
    UNRIPE = auto()
    RIPENING = auto()
    RIPE = auto()
    OVERRIPE = auto()


class HarvestResult(Enum):
    SUCCESS = auto()
    UNREACHABLE = auto()
    FAILED_GRASP = auto()
    FAILED_FORCE_THRESHOLD = auto()
    FRUIT_DAMAGED = auto()
    ABORTED = auto()


class ObstacleKind(Enum):
    TRACTOR = auto()
    WORKER = auto()
    ANIMAL = auto()
    UNKNOWN = auto()


@dataclass(frozen=True)
class Pose3D:
    """Dunya (map/odom) cercevesinde konum + yonelim (quaternion)."""
    x: float
    y: float
    z: float
    qx: float = 0.0
    qy: float = 0.0
    qz: float = 0.0
    qw: float = 1.0
    frame_id: str = "map"


@dataclass(frozen=True)
class BoundingBox2D:
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @property
    def center(self) -> Tuple[float, float]:
        return ((self.x_min + self.x_max) / 2.0, (self.y_min + self.y_max) / 2.0)


@dataclass(frozen=True)
class DetectionResult:
    """Tek bir algilama karesinin (frame) ciktisi: 2D kutu + varsa 3D konum."""
    class_id: int
    class_name: str
    confidence: float
    bbox: BoundingBox2D
    position_3d: Optional[Pose3D] = None  # derinlik verisi varsa doldurulur
    maturity: MaturityLevel = MaturityLevel.UNKNOWN
    track_id: Optional[int] = None


@dataclass(frozen=True)
class FruitTarget:
    """Manipulasyon katmanina iletilen, hasat edilecek tek bir meyve hedefi."""
    target_id: str
    fruit_type: str                 # "apple", ileride "pepper" vb. -> Factory anahtari
    pose: Pose3D
    maturity: MaturityLevel
    required_force_n: float = 4.5   # dalindan koparmak icin hedef kuvvet (Newton)
    max_force_n: float = 12.0       # bu degerin ustu -> meyveye zarar riski
    approach_offset_m: float = 0.12


@dataclass
class RowGeometry:
    """Sira takibi node'unun urettigi, kontrolcunun tukettigi ara temsil."""
    lateral_offset_m: float     # aracin sira merkezine gore yanal sapmasi
    heading_error_rad: float    # sira ekseni ile arac yonu arasindaki aci farki
    row_confidence: float       # 0..1, nokta bulutu segmentasyon guveni
    valid: bool = True
