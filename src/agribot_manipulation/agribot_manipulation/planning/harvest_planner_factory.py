"""HarvestPlannerFactory - Factory Pattern (meyve turune gore planlayici secimi)."""
from typing import Callable, Dict

from agribot_manipulation.planning.harvest_planner import AppleHarvestPlanner, HarvestPlanner
from agribot_manipulation.planning.moveit2_adapter import MoveIt2Adapter
from agribot_manipulation.control.force_controller import ForceController
from agribot_manipulation.control.end_effector_controller import EndEffectorController


class HarvestPlannerFactory:
    _registry: Dict[str, Callable[..., HarvestPlanner]] = {
        "apple": AppleHarvestPlanner,
    }

    @classmethod
    def register(cls, fruit_type: str, builder: Callable[..., HarvestPlanner]) -> None:
        cls._registry[fruit_type] = builder

    @classmethod
    def create(
        cls,
        fruit_type: str,
        moveit_adapter: MoveIt2Adapter,
        force_controller: ForceController,
        end_effector: EndEffectorController,
    ) -> HarvestPlanner:
        if fruit_type not in cls._registry:
            raise ValueError(f"Bilinmeyen fruit_type='{fruit_type}'. Mevcut: {list(cls._registry.keys())}")
        return cls._registry[fruit_type](moveit_adapter, force_controller, end_effector)
