gnome-terminal --window -e 'bash -c "source ~/.bashrc; roslaunch spirecv_ros gimbal_detection_with_tracking.launch;  exit ;exec bash"' \
--tab -e 'bash -c "sleep 2; source ~/.bashrc; roslaunch p450_experiment gimbal_yolov5_tracking.launch; exit ; exec bash"' \
