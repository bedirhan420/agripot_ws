"""
ConfigManager - Singleton Pattern (BILINCLI ve SINIRLI kullanim).

ONEMLI TASARIM NOTU
--------------------
Singleton genellikle test edilebilirligi bozdugu ve gizli global durum
yarattigi icin bir "anti-pattern" olarak elestirilir. Bu projede varsayilan
yaklasim Singleton DEGIL, Dependency Injection'dir: her node/sinif,
ihtiyac duydugu bagimliliklari (IDetector, INavigationStrategy, ...)
kurucusunda (constructor) parametre olarak alir; bu sayede unit testlerde
sahte (mock/fake) implementasyonlarla kolayca degistirilebilirler.

ConfigManager BURADA ISTISNAI OLARAK Singleton olarak tanimlanmistir,
cunku:
  1) Salt-okunur, degismez (immutable) statik konfigurasyon tasir
     (kamera intrinsikleri, model yollari, kuvvet esikleri gibi
     calisma-zamani boyunca degismeyen degerler).
  2) ROS2 parametre sunucusunun ustune ince bir "tip guvenli" katman
     kurar; birden fazla node ayni parametre setini ROS2 parametre
     servisini tekrar tekrar sorgulamadan okuyabilir.
  3) Mutable/paylasimli durum (ornegin robotun anlik hizi, gorev durumu)
     KESINLIKLE burada TUTULMAZ; bu tur durum MissionContext (State
     Pattern) ve node'larin kendi ic durumunda yasar.

Yeni bir konfigurasyon kaynagi gerekiyorsa, bu sinifi degistirmek yerine
IConfigSource arayuzunu implemente eden yeni bir kaynak enjekte edin
(Open/Closed Principle).
"""
import threading
from typing import Any, Dict, Optional


class ConfigManager:
    _instance: Optional["ConfigManager"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        if ConfigManager._instance is not None:
            raise RuntimeError(
                "ConfigManager dogrudan ornceklendirilemez; ConfigManager.instance() kullanin."
            )
        self._values: Dict[str, Any] = {}
        self._frozen = False

    @classmethod
    def instance(cls) -> "ConfigManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def load_from_dict(self, values: Dict[str, Any]) -> None:
        if self._frozen:
            raise RuntimeError("ConfigManager dondurulmus (frozen); calisma zamaninda degistirilemez.")
        self._values.update(values)

    def freeze(self) -> None:
        """Bringup asamasindan sonra cagrilir; bundan sonra deger degisikligine izin verilmez."""
        self._frozen = True

    def get(self, key: str, default: Any = None) -> Any:
        return self._values.get(key, default)

    def require(self, key: str) -> Any:
        if key not in self._values:
            raise KeyError(f"Zorunlu konfigurasyon anahtari eksik: '{key}'")
        return self._values[key]

    @classmethod
    def reset_for_testing(cls) -> None:
        """SADECE unit testlerde kullanilir; Singleton'in test izolasyonunu saglar."""
        with cls._lock:
            cls._instance = None
