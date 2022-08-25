## ego自主飞行脚本
gnome-terminal --window -e 'bash -c "roslaunch p450_experiment p450_mavros.launch; exec bash"' \
--tab -e 'bash -c "sleep 5; roslaunch realsense2_camera rs_d400_and_t265.launch; exec bash"' \
--tab -e 'bash -c "sleep 15; roslaunch prometheus_gazebo sitl_ego_planner.launch; exec bash"' \
--tab -e 'bash -c "sleep 20; roslaunch prometheus_gazebo sitl_ego_station.launch; exec bash"' \

