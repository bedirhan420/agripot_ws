"""MoveIt2 move_group ve manipulasyon (hasat) action sunucusunu baslatir."""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    bringup_share = get_package_share_directory('agribot_bringup')
    controllers_yaml = os.path.join(bringup_share, 'config', 'moveit2_controllers.yaml')

    # NOT: move_group dugumu tipik olarak MoveIt Setup Assistant'in urettigi
    # bir launch dosyasi (moveit_config paketi) uzerinden baslatilir. Burada
    # yalnizca iskelet/placeholder verilmistir; gercek projede
    # `agribot_moveit_config` paketi olusturulmalidir (bkz. ROADMAP Faz 7).
    move_group = Node(
        package='moveit_ros_move_group',
        executable='move_group',
        output='screen',
        parameters=[controllers_yaml],
    )

    manipulation_node = Node(
        package='agribot_manipulation',
        executable='manipulation_node',
        output='screen',
    )

    return LaunchDescription([move_group, manipulation_node])
