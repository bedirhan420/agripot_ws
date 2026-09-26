"""
MissionContext - State Pattern'in "context" nesnesi + Facade.

Bu sinif, State/Strategy nesnelerinin ihtiyac duydugu TUM ortam
sorgularini (algilama, konum, Nav2 durumu vb.) tek bir yerden sunar.
Node'lar (navigation_manager_node.py) bu context'i kurar ve donguyu
(tick) surdurur; States/Strategies rclpy'i DOGRUDAN GORMEZ (yalnizca
context uzerinden), bu da onlarin izole birim testini kolaylastirir.

Not: rclpy tipine bagimli metodlar (Twist, PoseStamped) yalnizca somut
donus/aktarim noktalarinda gorulur; context'in kendisi cogunlukla
"port" (bagimliligi disariya delege eden) bir sinif gibi davranir.
"""
from typing import Callable, List, Optional

from agribot_core.interfaces.observer import Subject
from agribot_core.interfaces.i_navigation_strategy import INavigationStrategy
from agribot_core.common.types import Pose3D
from agribot_navigation.state_machine.robot_state import IRobotState


class MissionContext(Subject):

    def __init__(
        self,
        cmd_vel_publisher: Callable,
        row_cloud_provider: Callable,
        pose_provider: Callable,
        harvest_target_provider: Callable,
        obstacle_detector: Callable,
        nav2_goal_sender: Callable,
        harvest_requester: Callable,
        home_pose: Pose3D,
    ):
        """
        Butun bagimliliklar constructor uzerinden enjekte edilir (Dependency
        Injection). Bu sayede navigation_manager_node.py disinda, gercek
        rclpy olmadan (sahte/fake fonksiyonlarla) bu sinif unit test edilebilir.
        """
        super().__init__()
        self._cmd_vel_publisher = cmd_vel_publisher
        self._row_cloud_provider = row_cloud_provider
        self._pose_provider = pose_provider
        self._harvest_target_provider = harvest_target_provider
        self._obstacle_detector = obstacle_detector
        self._nav2_goal_sender = nav2_goal_sender
        self._harvest_requester = harvest_requester
        self._home_pose = home_pose

        self._current_state: Optional[IRobotState] = None
        self._active_strategy: Optional[INavigationStrategy] = None
        self._start_requested = False
        self._harvest_complete = False
        self._fault_cleared = False

    # --- State Pattern cekirdek mekanizmasi -----------------------------------
    def transition_to(self, new_state: IRobotState) -> None:
        if self._current_state is not None:
            self._current_state.on_exit(self)
        old_name = self._current_state.name if self._current_state else "NONE"
        self._current_state = new_state
        self.notify("state_changed", {"from": old_name, "to": new_state.name})
        new_state.on_enter(self)

    def tick(self) -> None:
        """Sabit frekansli kontrol dongusunde (ornegin 20 Hz) cagrilir."""
        if self._current_state is None:
            from agribot_navigation.state_machine.states import IdleState
            self.transition_to(IdleState())
        self._current_state.handle(self)

    @property
    def current_state_name(self) -> str:
        return self._current_state.name if self._current_state else "NONE"

    # --- Strategy erisimi -------------------------------------------------
    def set_active_strategy(self, strategy: INavigationStrategy) -> None:
        self._active_strategy = strategy
        strategy.activate(self)

    def get_active_strategy(self) -> INavigationStrategy:
        return self._active_strategy

    def apply_navigation_command(self) -> None:
        cmd = self._active_strategy.compute_command(self)
        if cmd is not None:
            self._cmd_vel_publisher(cmd)

    def stop_robot(self) -> None:
        from geometry_msgs.msg import Twist
        self._cmd_vel_publisher(Twist())

    # --- Ortam sorgulari (States/Strategies tarafindan kullanilir) --------
    def get_latest_point_cloud(self):
        return self._row_cloud_provider()

    def get_current_pose(self) -> Pose3D:
        return self._pose_provider()

    def is_dynamic_obstacle_detected(self) -> bool:
        return self._obstacle_detector()

    def get_next_harvestable_target(self):
        return self._harvest_target_provider()

    def is_row_end_reached(self) -> bool:
        # TODO: RowDetector guven skorunun sureklu dusuk kaldigi / gorus alaninda
        # govde kalmadigi durumla tespit edilir.
        return False

    def compute_next_row_entry_pose(self) -> Pose3D:
        # TODO: tarla haritasi / onceden tanimli sira araligina gore hesapla.
        return self.get_current_pose()

    def is_field_coverage_complete(self) -> bool:
        # TODO: gorev planlayicidan (mission planner) gelen kapsama bilgisiyle degistir.
        return False

    def get_home_pose(self) -> Pose3D:
        return self._home_pose

    # --- Nav2 koprusu -------------------------------------------------------
    def send_nav2_goal(self, pose: Pose3D) -> None:
        self._nav2_goal_sender(pose)

    def is_nav2_goal_reached(self) -> bool:
        # NavigationManagerNode, Nav2 action sonucu geldiginde bu bayragi gunceller.
        return getattr(self, "_nav2_goal_reached", False)

    def enable_nav2_local_avoidance(self, safety_margin_m: float) -> None:
        # NavigationManagerNode, costmap inflation/safety parametrelerini
        # gerekirse dinamik olarak yukseltir.
        pass

    def is_path_clear_of_dynamic_obstacles(self) -> bool:
        return not self._obstacle_detector()

    # --- Yaklasma / Hasat kopruleri ------------------------------------------
    def begin_fine_approach(self, target) -> None:
        pass  # NavigationManagerNode ince yaklasma kontrolcusunu tetikler

    def continue_fine_approach(self) -> None:
        pass

    def is_fine_approach_complete(self) -> bool:
        return getattr(self, "_fine_approach_done", False)

    def request_harvest(self, target) -> None:
        self._harvest_complete = False
        self._harvest_requester(target, self._on_harvest_done)

    def _on_harvest_done(self, result) -> None:
        self._harvest_complete = True

    def is_harvest_complete(self) -> bool:
        return self._harvest_complete

    # --- Hata / operator -------------------------------------------------
    def is_start_requested(self) -> bool:
        return self._start_requested

    def request_start(self) -> None:
        self._start_requested = True

    def log_fault(self, reason: str) -> None:
        print(f"[MissionContext] FAULT: {reason}")  # gercekte node logger'ina yonlendirilir

    def notify_operator(self, reason: str) -> None:
        self.notify("fault", reason)

    def is_fault_cleared_by_operator(self) -> bool:
        return self._fault_cleared
