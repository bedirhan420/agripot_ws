"""EKF, Nav2 ve sira takibi/gorev yonetimi dugumlerini baslatir."""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    bringup_share = get_package_share_directory('agribot_bringup')
    ekf_params = os.path.join(bringup_share, 'config', 'ekf_params.yaml')
    nav2_params = os.path.join(bringup_share, 'config', 'nav2_params.yaml')

    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_params],
    )

    # Nav2, YALNIZCA dinamik engel kacinma (ObstacleAvoidanceStrategy) icin
    # kullanilir; birincil sira-ici kontrol RowFollowingStrategy'dedir
    # (bkz. docs/ARCHITECTURE.md, "Navigasyon katmani" bolumu).
    nav2_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('nav2_bringup'), 'launch', 'navigation_launch.py')
        ),
        launch_arguments={'params_file': nav2_params, 'use_sim_time': 'true'}.items(),
    )

    navigation_manager = Node(
        package='agribot_navigation',
        executable='navigation_manager_node',
        output='screen',
    )

    return LaunchDescription([ekf_node, nav2_bringup_launch, navigation_manager])
