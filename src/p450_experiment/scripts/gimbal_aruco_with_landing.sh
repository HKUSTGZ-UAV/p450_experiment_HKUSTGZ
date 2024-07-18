gnome-terminal --window -e 'bash -c "roslaunch p450_experiment gimbal_server.launch; exec bash"' \
--tab -e 'bash -c "sleep 2; roslaunch p450_experiment g1_aruco_clicked_tracking.launch; exec bash"' \
--tab -e 'bash -c "sleep 4; roslaunch p450_experiment gimbal_aruco_with_landing.launch; exec bash"' \
