#!/bin/bash
catkin_make --source src/Prometheus/Modules/common --build build/common
catkin_make --source src/Prometheus/Modules/uav_control --build build/uav_control
catkin_make --source src/Prometheus/Modules/communication --build build/communication
catkin_make --source src/Prometheus/Modules/tutorial_demo --build build/tutorial_demo
catkin_make --source src/p450_experiment --build build/p450_experiment

# for realsense-ros
catkin_make --source src/realsense-ros/realsense2_camera --build build/realsense2_camera
catkin_make --source src/realsense-ros/realsense2_description --build build/realsense2_description

# for mission
catkin_make --source src/mission --build build/mission

# for planning
catkin_make --source src/Prometheus/Modules/simulator_utils --build build/simulator_utils
catkin_make --source src/Prometheus/Modules/ego_planner_swarm --build build/ego_planner_swarm
catkin_make --source src/Prometheus/Modules/motion_planning --build build/motion_planning
catkin_make --source src/Prometheus/Modules/FAST_LIO --build build/FAST_LIO

# for bluesea2
# catkin_make --source src/bluesea2 --build build/bluesea2

# for rplidar
# catkin_make --source src/rplidar_ros --build build/rplidar_ros

# for livox_ros_driver2
catkin_make --source src/livox_ros_driver2 --build build/livox_ros_driver2 -DROS_EDITION=ROS1
