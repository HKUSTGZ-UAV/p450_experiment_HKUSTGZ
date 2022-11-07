#!/bin/bash

gnome-terminal --window -e 'bash -c "roslaunch p450_experiment mipi_veye327.launch; exec bash"' \
--tab -e 'bash -c "sleep 5; source /home/amov/catkin_workspace/install/setup.bash --extend; roslaunch p450_experiment siamRPN.launch; exec bash"' \
--tab -e 'bash -c "sleep 15; roslaunch p450_experiment rtsp.launch; exec bash"' \
