gnome-terminal --window -e 'bash -c "source /opt/ros/noetic/setup.bash  && source ~/p450_experiment/devel/setup.bash && roslaunch p450_experiment p450_communication.launch; exec bash"' \
--tab -e 'bash -c "sleep 3; source ~/.bashrc;source /opt/ros/noetic/setup.bash; roslaunch rosbridge_server rosbridge_websocket.launch; exec bash"' \
