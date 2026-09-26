"""YOLOv8 tabanli algilama dugumunu baslatir."""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    bringup_share = get_package_share_directory('agribot_bringup')
    params_file = os.path.join(bringup_share, 'config', 'yolov8_params.yaml')

    perception_node = Node(
        package='agribot_perception',
        executable='perception_node',
        parameters=[params_file],
        output='screen',
    )
    return LaunchDescription([perception_node])
