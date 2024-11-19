#!/bin/bash
catkin_make --source src/Prometheus/Modules/common --build build/common
catkin_make --source src/Prometheus/Modules/uav_control --build build/uav_control
catkin_make --source src/Prometheus/Modules/communication --build build/communication
catkin_make --source src/Prometheus/Modules/tutorial_demo --build build/tutorial_demo
catkin_make --source src/p450_experiment --build build/p450_experiment
