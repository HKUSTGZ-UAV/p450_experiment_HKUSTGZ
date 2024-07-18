gnome-terminal --window -e 'bash -c "source ~/.bashrc; roslaunch p450_experiment gimbal_server.launch; exec bash"' \
--tab -e 'bash -c "sleep 2; source ~/.bashrc; roslaunch p450_experiment gimbal_detection_with_tracking.launch; exec bash"' \
--tab -e 'bash -c "sleep 4; source ~/.bashrc; roslaunch p450_experiment gimbal_yolov5_tracking_g1.launch; exec bash"' \
