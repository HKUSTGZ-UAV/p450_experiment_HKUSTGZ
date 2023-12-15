gnome-terminal --window -e 'bash -c "roscore; exec bash"' \
--tab -e 'bash -c "sleep 6; roslaunch p450_experiment P450_outdoor_onboard.launch; exec bash"' \
--tab -e 'bash -c "sleep 6; roslaunch p450_experiment rs_camera_d435i.launch; exec bash"' \
--tab -e 'bash -c "sleep 10; roslaunch p450_experiment ego_planner_depth_outdoor.launch; exec bash"' \
--tab -e 'bash -c "sleep 12; source ~/.bashrc; roslaunch p450_experiment rviz_d435i.launch; exec bash"' \
