#!/bin/bash
# 脚本名称: mavros vins bringup
# 脚本描述: 该脚本为起飞&降落控制demo启动脚本,包含PX4 SITL,Gazebo仿真环境,无人机控制节点以及起飞&降落控制节点

gnome-terminal --window -e 'bash -c "roscore; exec bash"' \
--tab -e 'bash -c "sleep 5; roslaunch p250_experiment uav_control_main_indoor_vins.launch; exec bash"' \
--tab -e 'bash -c "sleep 10; rosservice call /uav1/mavros/set_stream_rate 0 15 1; exec bash"' \
--tab -e 'bash -c "sleep 20; rosservice call /uav1/mavros/cmd/command "{broadcast: false, command: 511, confirmation: 0, param1: 105, param2: 5000, param3: 0.0, param4: 0.0, param5: 0.0, param6: 0.0, param7: 0.0}"; exec bash"' \
--tab -e 'bash -c "sleep 24; roslaunch p250_experiment rs_camera_720p.launch; exec bash"' \
