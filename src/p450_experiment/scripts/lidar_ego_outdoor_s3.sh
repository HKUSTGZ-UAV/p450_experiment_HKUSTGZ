gnome-terminal --window -e 'bash -c "roslaunch p450_experiment rplidar_s3.launch; exec bash"' \
--tab -e 'bash -c "sleep 2; roslaunch p450_experiment filter_lidar.launch; exec bash"' \
--tab -e 'bash -c "sleep 4; roslaunch p450_experiment scan_to_octomap_outdoor.launch; exec bash"' \
--tab -e 'bash -c "sleep 6; roslaunch p450_experiment ego_planner_octomap_outdoor.launch; exec bash"' \
--tab -e 'bash -c "sleep 8; source ~/.bashrc; roslaunch p450_experiment rviz_2dlidar.launch; exec bash"' \
