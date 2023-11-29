#!/bin/bash
roslaunch p450_experiment uav_control_main_indoor_vins.launch
sleep 5
rosservice call /uav1/mavros/set_stream_rate 0 15 1
rosservice call /uav1/mavros/cmd/command "{broadcast: false, command: 511, confirmation: 0, param1: 105, param2: 5000, param3: 0.0, param4: 0.0, param5: 0.0, param6: 0.0, param7: 0.0}"
roslaunch p450_experiment rs_camera_720p.launch

