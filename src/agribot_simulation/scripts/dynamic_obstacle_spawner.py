#!/usr/bin/env python3
"""
DynamicObstacleSpawner - Factory Pattern.

Proje dokumaninda belirtilen iki yontemi de destekler:
  1) Gazebo native "actor" (onceden tanimli/animasyonlu yuruyus, ör. isci),
  2) Python tarafinda rastgele yorungede hareket eden basit collision-box'lar
     (traktor/hayvan gibi rijit-govde nesneler icin daha uygun).

ObstacleFactory, engel TURUNE (ObstacleKind) gore dogru spawn stratejisini
secer; NavigationManagerNode ve simulasyon kurulum script'leri bu factory'yi
CAGIRIR, engelin nasil spawn edildigini bilmek zorunda degildir.

Kullanim:
    ros2 run agribot_simulation dynamic_obstacle_spawner.py --ros-args -p obstacle_count:=3
"""
import random
from abc import ABC, abstractmethod
from typing import Callable, Dict, List

import rclpy
from rclpy.node import Node

from agribot_core.common.types import ObstacleKind, Pose3D
from agribot_simulation.backends.gazebo_backend import GazeboSimBackend


class IObstacleSpawnStrategy(ABC):
    @abstractmethod
    def spawn(self, backend: GazeboSimBackend, name: str, spawn_pose: Pose3D) -> bool:
        raise NotImplementedError

    @abstractmethod
    def update(self, backend: GazeboSimBackend, name: str, dt: float) -> None:
        """Her kontrol dongusunde cagrilir; ornegin collision-box'i hareket ettirir."""
        raise NotImplementedError


class ActorObstacleStrategy(IObstacleSpawnStrategy):
    """Gazebo'nun native actor+trajectory sistemine dayanir; hareket SDF icinde tanimlidir."""

    def __init__(self, model_uri: str = "model://dynamic_worker_actor"):
        self._model_uri = model_uri

    def spawn(self, backend: GazeboSimBackend, name: str, spawn_pose: Pose3D) -> bool:
        return backend.spawn_entity(name, self._model_uri, spawn_pose)

    def update(self, backend: GazeboSimBackend, name: str, dt: float) -> None:
        pass  # hareket SDF <trajectory> icinde Gazebo tarafindan yonetilir


class RandomWalkBoxStrategy(IObstacleSpawnStrategy):
    """Python tarafinda rastgele yorungeli basit bir collision-box (ornegin traktor)."""

    def __init__(self, model_uri: str = "model://simple_collision_box", area_half_size_m: float = 5.0):
        self._model_uri = model_uri
        self._area_half_size = area_half_size_m
        self._targets: Dict[str, Pose3D] = {}

    def spawn(self, backend: GazeboSimBackend, name: str, spawn_pose: Pose3D) -> bool:
        self._targets[name] = self._random_target()
        return backend.spawn_entity(name, self._model_uri, spawn_pose)

    def update(self, backend: GazeboSimBackend, name: str, dt: float) -> None:
        # TODO: `gz service .../set_pose` ile mevcut pozdan hedefe dogru
        # kucuk adimlarla ilerlet; hedefe ulasildiginda yeni rastgele hedef sec.
        current_pose, ok = backend.get_entity_pose(name)
        if not ok:
            return
        target = self._targets.get(name)
        if target is None:
            return
        distance = ((current_pose.x - target.x) ** 2 + (current_pose.y - target.y) ** 2) ** 0.5
        if distance < 0.2:
            self._targets[name] = self._random_target()

    def _random_target(self) -> Pose3D:
        return Pose3D(
            x=random.uniform(-self._area_half_size, self._area_half_size),
            y=random.uniform(-self._area_half_size, self._area_half_size),
            z=0.0,
        )


class ObstacleFactory:
    """Factory Pattern: ObstacleKind -> IObstacleSpawnStrategy."""

    _registry: Dict[ObstacleKind, Callable[[], IObstacleSpawnStrategy]] = {
        ObstacleKind.WORKER: ActorObstacleStrategy,
        ObstacleKind.TRACTOR: lambda: RandomWalkBoxStrategy(model_uri="model://simple_collision_box_tractor"),
        ObstacleKind.ANIMAL: lambda: RandomWalkBoxStrategy(model_uri="model://simple_collision_box_animal"),
    }

    @classmethod
    def create_strategy(cls, kind: ObstacleKind) -> IObstacleSpawnStrategy:
        if kind not in cls._registry:
            raise ValueError(f"Bilinmeyen engel turu: {kind}")
        return cls._registry[kind]()


class DynamicObstacleSpawnerNode(Node):

    def __init__(self):
        super().__init__("dynamic_obstacle_spawner")
        self.declare_parameter("obstacle_count", 2)
        self.declare_parameter("update_rate_hz", 2.0)

        self._backend = GazeboSimBackend()
        self._backend.connect()

        self._active: List[tuple] = []  # (name, strategy)
        count = self.get_parameter("obstacle_count").value
        kinds = [ObstacleKind.WORKER, ObstacleKind.TRACTOR, ObstacleKind.ANIMAL]

        for i in range(count):
            kind = kinds[i % len(kinds)]
            strategy = ObstacleFactory.create_strategy(kind)
            name = f"dyn_obstacle_{kind.name.lower()}_{i}"
            spawn_pose = Pose3D(x=float(i * 2), y=4.0, z=0.0)
            if strategy.spawn(self._backend, name, spawn_pose):
                self._active.append((name, strategy))
                self.get_logger().info(f"Spawn edildi: {name}")

        dt = 1.0 / float(self.get_parameter("update_rate_hz").value)
        self.create_timer(dt, self._update_loop)

    def _update_loop(self) -> None:
        for name, strategy in self._active:
            strategy.update(self._backend, name, dt=1.0)


def main(args=None):
    rclpy.init(args=args)
    node = DynamicObstacleSpawnerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
