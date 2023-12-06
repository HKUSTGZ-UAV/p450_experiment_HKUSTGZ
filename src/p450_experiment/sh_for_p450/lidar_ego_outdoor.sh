gnome-terminal --window -e 'bash -c "roscore; exec bash"' \
--tab -e 'bash -c "sleep 6; roslaunch p450_experiment P450_outdoor_onboard.launch; exec bash"' \
--tab -e 'bash -c "sleep 6; roslaunch p450_experiment LDS-50C-3.launch; exec bash"' \
--tab -e 'bash -c "sleep 6; roslaunch p450_experiment filter_lidar.launch; exec bash"' \
--tab -e 'bash -c "sleep 8; roslaunch p450_experiment scan_to_octomap.launch; exec bash"' \
--tab -e 'bash -c "sleep 10; roslaunch p450_experiment ego_planner_octomap.launch; exec bash"' \
--tab -e 'bash -c "sleep 12; source ~/.bashrc; roslaunch p450_experiment rviz_2dlidar.launch; exec bash"' \
