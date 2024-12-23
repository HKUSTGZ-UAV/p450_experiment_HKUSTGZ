gnome-terminal --window -e 'bash -c "source ~/.bashrc; roslaunch p450_experiment aruco_detection_with_d435i.launch; exec bash"' \
--tab -e 'bash -c "sleep 3; source ~/.bashrc; roslaunch p450_experiment aruco_tracking.launch; exec bash"' \
