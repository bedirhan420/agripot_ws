cmake_minimum_required(VERSION 3.8)
project(agribot_simulation)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

install(DIRECTORY worlds models mujoco DESTINATION share/${PROJECT_NAME})

ament_python_install_package(backends)

install(PROGRAMS
  scripts/dynamic_obstacle_spawner.py
  scripts/mud_friction_randomizer.py
  scripts/breakable_joint_manager.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
