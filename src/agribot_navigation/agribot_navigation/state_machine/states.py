"""
Somut robot durumlari (State Pattern).

Gecis diyagrami (ozet):

    IdleState --start--> RowFollowingState
    RowFollowingState --meyve tespit edildi & ulasilabilir--> ApproachingFruitState
    RowFollowingState --dinamik engel--> ObstacleAvoidanceState
    RowFollowingState --sira sonu--> WaypointTurnState
    ApproachingFruitState --hedefe ulasildi--> HarvestingState
    HarvestingState --tamam/basarisiz--> RowFollowingState  (kuyrukta baska meyve varsa
                                                              ApproachingFruitState'e tekrar gecebilir)
    ObstacleAvoidanceState --yol acildi--> RowFollowingState
    WaypointTurnState --donus tamam--> RowFollowingState  (siradaki satir)
    Herhangi bir durum --kritik hata / operator durdurma--> FaultState
"""
from agribot_navigation.state_machine.robot_state import IRobotState
from agribot_navigation.strategies.navigation_strategy_factory import NavigationStrategyFactory


class IdleState(IRobotState):
    name = "IDLE"

    def on_enter(self, context) -> None:
        context.stop_robot()

    def handle(self, context) -> None:
        if context.is_start_requested():
            context.transition_to(RowFollowingState())

    def on_exit(self, context) -> None:
        pass


class RowFollowingState(IRobotState):
    name = "ROW_FOLLOWING"

    def on_enter(self, context) -> None:
        context.set_active_strategy(NavigationStrategyFactory.create("row_following"))

    def handle(self, context) -> None:
        if context.is_dynamic_obstacle_detected():
            context.transition_to(ObstacleAvoidanceState())
            return

        harvestable = context.get_next_harvestable_target()
        if harvestable is not None:
            context.transition_to(ApproachingFruitState(target=harvestable))
            return

        if context.get_active_strategy().is_finished(context):
            context.transition_to(WaypointTurnState())
            return

        context.apply_navigation_command()

    def on_exit(self, context) -> None:
        pass


class ApproachingFruitState(IRobotState):
    name = "APPROACHING_FRUIT"

    def __init__(self, target):
        self._target = target

    def on_enter(self, context) -> None:
        context.begin_fine_approach(self._target)

    def handle(self, context) -> None:
        if context.is_dynamic_obstacle_detected():
            context.transition_to(ObstacleAvoidanceState())
            return
        if context.is_fine_approach_complete():
            context.transition_to(HarvestingState(target=self._target))
        else:
            context.continue_fine_approach()

    def on_exit(self, context) -> None:
        pass


class HarvestingState(IRobotState):
    name = "HARVESTING"

    def __init__(self, target):
        self._target = target

    def on_enter(self, context) -> None:
        context.stop_robot()  # hasat sirasinda govde sabit kalir
        context.request_harvest(self._target)

    def handle(self, context) -> None:
        if context.is_harvest_complete():
            context.transition_to(RowFollowingState())

    def on_exit(self, context) -> None:
        pass


class ObstacleAvoidanceState(IRobotState):
    name = "OBSTACLE_AVOIDANCE"

    def on_enter(self, context) -> None:
        context.set_active_strategy(NavigationStrategyFactory.create("obstacle_avoidance"))

    def handle(self, context) -> None:
        if context.get_active_strategy().is_finished(context):
            context.transition_to(RowFollowingState())
        else:
            context.apply_navigation_command()

    def on_exit(self, context) -> None:
        pass


class WaypointTurnState(IRobotState):
    name = "WAYPOINT_TURN"

    def on_enter(self, context) -> None:
        strategy = NavigationStrategyFactory.create("waypoint")
        strategy.set_goal(context.compute_next_row_entry_pose())
        context.set_active_strategy(strategy)

    def handle(self, context) -> None:
        if context.get_active_strategy().is_finished(context):
            if context.is_field_coverage_complete():
                context.transition_to(ReturningHomeState())
            else:
                context.transition_to(RowFollowingState())
        else:
            context.apply_navigation_command()

    def on_exit(self, context) -> None:
        pass


class ReturningHomeState(IRobotState):
    name = "RETURNING_HOME"

    def on_enter(self, context) -> None:
        strategy = NavigationStrategyFactory.create("waypoint")
        strategy.set_goal(context.get_home_pose())
        context.set_active_strategy(strategy)

    def handle(self, context) -> None:
        if context.get_active_strategy().is_finished(context):
            context.transition_to(IdleState())
        else:
            context.apply_navigation_command()

    def on_exit(self, context) -> None:
        pass


class FaultState(IRobotState):
    name = "FAULT"

    def __init__(self, reason: str = ""):
        self._reason = reason

    def on_enter(self, context) -> None:
        context.stop_robot()
        context.log_fault(self._reason)
        context.notify_operator(self._reason)

    def handle(self, context) -> None:
        if context.is_fault_cleared_by_operator():
            context.transition_to(IdleState())

    def on_exit(self, context) -> None:
        pass
