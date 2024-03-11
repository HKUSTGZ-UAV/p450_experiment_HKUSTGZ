gnome-terminal --window -e 'bash -c "source /opt/ros/noetic/setup.bash && source ~/p450_experiment/devel/setup.bash && roslaunch p450_experiment P450_outdoor_communication_gps.launch; exec bash"' \
