"""NavigationStrategyFactory - Factory Pattern (navigasyon stratejileri icin)."""
from typing import Callable, Dict

from agribot_core.interfaces.i_navigation_strategy import INavigationStrategy
from agribot_navigation.strategies.row_following_strategy import RowFollowingStrategy
from agribot_navigation.strategies.waypoint_strategy import WaypointStrategy
from agribot_navigation.strategies.obstacle_avoidance_strategy import ObstacleAvoidanceStrategy


class NavigationStrategyFactory:
    _registry: Dict[str, Callable[..., INavigationStrategy]] = {
        "row_following": RowFollowingStrategy,
        "waypoint": WaypointStrategy,
        "obstacle_avoidance": ObstacleAvoidanceStrategy,
    }

    @classmethod
    def register(cls, name: str, builder: Callable[..., INavigationStrategy]) -> None:
        cls._registry[name] = builder

    @classmethod
    def create(cls, name: str, **kwargs) -> INavigationStrategy:
        if name not in cls._registry:
            raise ValueError(f"Bilinmeyen strateji: '{name}'. Mevcut: {list(cls._registry.keys())}")
        return cls._registry[name](**kwargs)
