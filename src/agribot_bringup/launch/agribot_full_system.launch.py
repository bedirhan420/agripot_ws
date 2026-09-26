"""Tum sistemi (simulasyon + algi + navigasyon + manipulasyon) tek komutla baslatir."""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def _include(pkg_share, filename):
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_share, 'launch', filename))
    )


def generate_launch_description():
    bringup_share = get_package_share_directory('agribot_bringup')

    return LaunchDescription([
        _include(bringup_share, 'agribot_simulation.launch.py'),
        _include(bringup_share, 'agribot_perception.launch.py'),
        _include(bringup_share, 'agribot_navigation.launch.py'),
        _include(bringup_share, 'agribot_manipulation.launch.py'),
    ])
