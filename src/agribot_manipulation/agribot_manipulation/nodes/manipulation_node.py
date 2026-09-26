"""
ManipulationNode - HarvestFruit action sunucusu (Facade).

agribot_msgs/action/HarvestFruit hedeflerini alir, HarvestPlannerFactory
ile meyve turune uygun planlayiciyi kurar, bunu bir HarvestFruitCommand'a
sarar ve CommandInvoker uzerinden calistirir. Ilerleme (feedback) her
asamada (approaching/aligning/grasping/...) yayinlanir.
"""
import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

from agribot_core.common.types import FruitTarget, MaturityLevel, Pose3D
from agribot_manipulation.planning.moveit2_adapter import MoveIt2Adapter
from agribot_manipulation.planning.harvest_planner_factory import HarvestPlannerFactory
from agribot_manipulation.control.force_controller import ForceController
from agribot_manipulation.control.end_effector_controller import EndEffectorController
from agribot_manipulation.commands.harvest_command import HarvestFruitCommand
from agribot_manipulation.commands.command_invoker import CommandInvoker

from agribot_msgs.action import HarvestFruit


class ManipulationNode(Node):

    def __init__(self):
        super().__init__("manipulation_node")

        self._moveit_adapter = MoveIt2Adapter(planning_group="agribot_arm")

        # TODO: gercek F/T sensor topic'i ve efor publisher'i ile degistir.
        self._force_controller = ForceController(
            read_force_n=lambda: 0.0,
            apply_effort=lambda effort: None,
        )
        self._end_effector = EndEffectorController(send_gripper_command=lambda pos, effort: True)

        self._invoker = CommandInvoker(max_retries=2, on_command_done=self._on_command_done)

        self._action_server = ActionServer(
            self, HarvestFruit, "harvest_fruit", execute_callback=self._execute_harvest_goal
        )
        self.get_logger().info("ManipulationNode hazir; HarvestFruit action sunucusu acik.")

    def _on_command_done(self, command: HarvestFruitCommand) -> None:
        self.get_logger().info(f"{command.describe()} -> {command.result}")

    def _execute_harvest_goal(self, goal_handle):
        det = goal_handle.request.target

        target = FruitTarget(
            target_id=det.track_id,
            fruit_type=det.fruit_type,
            pose=Pose3D(
                x=det.pose_3d.pose.position.x,
                y=det.pose_3d.pose.position.y,
                z=det.pose_3d.pose.position.z,
                frame_id=det.pose_3d.header.frame_id,
            ),
            maturity=MaturityLevel.RIPE,
        )

        planner = HarvestPlannerFactory.create(
            target.fruit_type, self._moveit_adapter, self._force_controller, self._end_effector
        )
        command = HarvestFruitCommand(planner, target)
        self._invoker.enqueue(command)

        feedback = HarvestFruit.Feedback()
        feedback.current_phase = HarvestFruit.Feedback.PHASE_APPROACHING
        feedback.progress = 0.1
        goal_handle.publish_feedback(feedback)

        result_enum = self._invoker.run_next()

        result = HarvestFruit.Result()
        result.result = self._to_action_result_code(result_enum)
        goal_handle.succeed()
        return result

    @staticmethod
    def _to_action_result_code(result_enum) -> int:
        from agribot_core.common.types import HarvestResult
        mapping = {
            HarvestResult.SUCCESS: HarvestFruit.Result.RESULT_SUCCESS,
            HarvestResult.UNREACHABLE: HarvestFruit.Result.RESULT_UNREACHABLE,
            HarvestResult.FAILED_GRASP: HarvestFruit.Result.RESULT_FAILED_GRASP,
            HarvestResult.FAILED_FORCE_THRESHOLD: HarvestFruit.Result.RESULT_FAILED_FORCE_THRESHOLD,
            HarvestResult.FRUIT_DAMAGED: HarvestFruit.Result.RESULT_FRUIT_DAMAGED,
        }
        return mapping.get(result_enum, HarvestFruit.Result.RESULT_UNREACHABLE)


def main(args=None):
    rclpy.init(args=args)
    node = ManipulationNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
