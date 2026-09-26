"""
HarvestPlanner - Template Method Pattern.

execute_harvest() SABIT adim sirasini tanimlar; her adimin NASIL
yapilacagi alt siniflarda (ornegin AppleHarvestPlanner) override edilir.
Bu, farkli meyve turleri (ileride biber, domates vb.) icin ayni akisi
tekrar yazmadan yeni bir alt sinif eklemeyi saglar (Open/Closed).
"""
from abc import ABC, abstractmethod

from agribot_core.common.types import FruitTarget, HarvestResult, Pose3D
from agribot_manipulation.planning.moveit2_adapter import MoveIt2Adapter
from agribot_manipulation.control.force_controller import ForceController
from agribot_manipulation.control.end_effector_controller import EndEffectorController


class HarvestPlanner(ABC):

    def execute_harvest(self, target: FruitTarget) -> HarvestResult:
        """SABIT iskelet -- alt siniflar bunu OVERRIDE ETMEZ."""
        if not self._pre_check(target):
            return HarvestResult.UNREACHABLE

        approach_pose = self._compute_approach_pose(target)
        if not self._move_to(approach_pose):
            return HarvestResult.UNREACHABLE

        if not self._align_gripper(target):
            self._retract()
            return HarvestResult.FAILED_GRASP

        if not self._grasp():
            self._retract()
            return HarvestResult.FAILED_GRASP

        achieved_force = self._apply_detachment_force(target)
        if achieved_force < target.required_force_n * 0.8:
            self._retract()
            return HarvestResult.FAILED_FORCE_THRESHOLD
        if achieved_force > target.max_force_n:
            self._retract()
            return HarvestResult.FRUIT_DAMAGED

        success = self._verify_fruit_in_gripper()
        self._retract()
        return HarvestResult.SUCCESS if success else HarvestResult.FAILED_GRASP

    # --- Hook metodlari: alt siniflar implemente eder --------------------
    @abstractmethod
    def _pre_check(self, target: FruitTarget) -> bool: ...
    @abstractmethod
    def _compute_approach_pose(self, target: FruitTarget) -> Pose3D: ...
    @abstractmethod
    def _move_to(self, pose: Pose3D) -> bool: ...
    @abstractmethod
    def _align_gripper(self, target: FruitTarget) -> bool: ...
    @abstractmethod
    def _grasp(self) -> bool: ...
    @abstractmethod
    def _apply_detachment_force(self, target: FruitTarget) -> float: ...
    @abstractmethod
    def _verify_fruit_in_gripper(self) -> bool: ...
    @abstractmethod
    def _retract(self) -> None: ...


class AppleHarvestPlanner(HarvestPlanner):
    """Elma hasadi icin somut adimlar."""

    def __init__(
        self,
        moveit_adapter: MoveIt2Adapter,
        force_controller: ForceController,
        end_effector: EndEffectorController,
    ):
        self._moveit = moveit_adapter
        self._force_controller = force_controller
        self._end_effector = end_effector

    def _pre_check(self, target: FruitTarget) -> bool:
        return self._moveit.is_pose_reachable(target.pose)

    def _compute_approach_pose(self, target: FruitTarget) -> Pose3D:
        return self._moveit.compute_approach_pose(target.pose, target.approach_offset_m)

    def _move_to(self, pose: Pose3D) -> bool:
        if not self._moveit.plan_to_pose(pose):
            return False
        return self._moveit.execute_last_plan()

    def _align_gripper(self, target: FruitTarget) -> bool:
        return self._moveit.plan_to_pose(target.pose) and self._moveit.execute_last_plan()

    def _grasp(self) -> bool:
        return self._end_effector.close_with_grip_force(grip_force_n=2.5)

    def _apply_detachment_force(self, target: FruitTarget) -> float:
        result = self._force_controller.apply_target_force(
            target_force_n=target.required_force_n, max_force_n=target.max_force_n
        )
        return result.achieved_force_n

    def _verify_fruit_in_gripper(self) -> bool:
        # TODO: gripper'daki basinc/mesafe sensoruyle veya kamera ile dogrula.
        return True

    def _retract(self) -> None:
        self._end_effector.open()
        # TODO: onceden tanimli guvenli (home) poza donus plani.
