"""
HarvestFruitCommand - Command Pattern.

Tek bir hasat girisimini bir nesneye donusturur. Bu sayede:
  - CommandInvoker kuyruklayabilir, yeniden deneyebilir (retry), loglayabilir,
  - basarisizlikta undo() ile kol guvenli pozisyona geri alinir,
ManipulationNode ise yalnizca "bir komut olustur ve calistir" der;
HASAT DETAYLARINI (HarvestPlanner) bilmez (Single Responsibility).
"""
from agribot_core.interfaces.i_harvest_command import IHarvestCommand
from agribot_core.common.types import FruitTarget, HarvestResult
from agribot_manipulation.planning.harvest_planner import HarvestPlanner


class HarvestFruitCommand(IHarvestCommand):

    def __init__(self, planner: HarvestPlanner, target: FruitTarget):
        self._planner = planner
        self._target = target
        self._result: HarvestResult = None

    def execute(self) -> HarvestResult:
        self._result = self._planner.execute_harvest(self._target)
        return self._result

    def undo(self) -> None:
        # HarvestPlanner.execute_harvest zaten basarisizlikta _retract() cagirir;
        # undo() burada operator tarafindan MANUEL iptal durumu icin tutulur.
        self._planner._retract()  # noqa: SLF001 -- Command, Planner'in "iptal" hook'una kasitli erisir

    def describe(self) -> str:
        return f"HarvestFruitCommand(target={self._target.target_id}, fruit={self._target.fruit_type})"

    @property
    def result(self) -> HarvestResult:
        return self._result

    @property
    def target(self) -> FruitTarget:
        return self._target
