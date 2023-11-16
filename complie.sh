#!/bin/bash
catkin_make --source src/Prometheus/Modules/common --build build/common
catkin_make --source src/Prometheus/Modules/uav_control --build build/uav_control
#catkin_make --source src/Prometheus/Modules/object_detection --build build/object_detection
catkin_make --source src/Prometheus/Modules/communication --build build/communication
#catkin_make --source src/object_circlex_detection --build build/object_circlex_detection
#catkin_make --source src/gimbal_control/src/gimbal_control --build build/gimbal_control
catkin_make --source src/p250_experiment --build build/p250_experiment
#catkin_make --source src/mission --build build/mission
#./src/siamprn_object_tracking/complie.sh && \
#catkin_make --source src/siamprn_object_tracking/ros/src/track_ros --build build/siamrpn_track

# for spirecv-ros
release_num=$(lsb_release -r --short)
echo $release_num
if [ $release_num == "18.04" ]
then
  catkin_make --source src/spirecv-ros/cv_bridge_1804 --build build/cv_bridge
else
  catkin_make --source src/spirecv-ros/cv_bridge_2004 --build build/cv_bridge
fi
catkin_make --source src/spirecv-ros/sv-msgs --build build/msgs
catkin_make --source src/spirecv-ros/sv-srvs --build build/srvs
catkin_make --source src/spirecv-ros/sv-rosapp --build build/rosapp

# for realsense-ros
catkin_make --source src/realsense-ros/realsense2_camera --build build/realsense2_camera
catkin_make --source src/realsense-ros/realsense2_description --build build/realsense2_description

# for mission
catkin_make --source src/mission --build build/mission

# for planning
catkin_make --source src/Prometheus/Modules/simulator_utils --build build/simulator_utils
catkin_make --source src/Prometheus/Modules/ego_planner_swarm --build build/ego_planner_swarm
catkin_make --source src/Prometheus/Modules/motion_planning --build build/motion_planning

# for vins-fusion
#catkin_make --source src/vins-fusion --build build/vins-fusion
