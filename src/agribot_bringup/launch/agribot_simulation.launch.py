"""Gazebo dunyasini baslatir, robotu spawn eder ve dinamik engel/camur script'lerini calistirir."""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    sim_share = get_package_share_directory('agribot_simulation')
    desc_share = get_package_share_directory('agribot_description')

    world_path = os.path.join(sim_share, 'worlds', 'orchard_row_world.sdf')
    xacro_path = os.path.join(desc_share, 'urdf', 'agribot.urdf.xacro')

    gz_sim = ExecuteProcess(
        cmd=['gz', 'sim', '-r', world_path],
        output='screen',
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': ('xacro ' + xacro_path)}],
        output='screen',
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description', '-name', 'agribot', '-z', '0.2'],
        output='screen',
    )

    # ROS2 <-> gz-sim topic koprusu (cmd_vel, odometry, camera, imu, gps)
    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            '/wheel/odometry@nav_msgs/msg/Odometry@gz.msgs.Odometry',
            '/imu@sensor_msgs/msg/Imu@gz.msgs.IMU',
            '/gps/fix@sensor_msgs/msg/NavSatFix@gz.msgs.NavSat',
            '/camera/color/image_raw@sensor_msgs/msg/Image@gz.msgs.Image',
            '/camera/depth/image_rect_raw@sensor_msgs/msg/Image@gz.msgs.Image',
            '/camera/depth/points@sensor_msgs/msg/PointCloud2@gz.msgs.PointCloudPacked',
            '/camera/color/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo',
        ],
        output='screen',
    )

    dynamic_obstacles = Node(
        package='agribot_simulation',
        executable='dynamic_obstacle_spawner.py',
        parameters=[{'obstacle_count': 2}],
        output='screen',
    )

    mud_randomizer = Node(
        package='agribot_simulation',
        executable='mud_friction_randomizer.py',
        parameters=[{'num_patches': 3}],
        output='screen',
    )

    breakable_joint_manager = Node(
        package='agribot_simulation',
        executable='breakable_joint_manager.py',
        output='screen',
    )

    return LaunchDescription([
        gz_sim,
        robot_state_publisher,
        spawn_robot,
        ros_gz_bridge,
        dynamic_obstacles,
        mud_randomizer,
        breakable_joint_manager,
    ])
