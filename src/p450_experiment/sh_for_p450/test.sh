gnome-terminal --window -e 'bash -c "roscore; exec bash"' \
--tab -e 'bash -c "sleep 4; roslaunch p450_experiment rs_t265.launch; exec bash"' \
--tab -e 'bash -c "sleep 6; roslaunch p450_experiment P450_indoor_onboard.launch; exec bash"' \
--tab -e 'bash -c "sleep 6; roslaunch p450_experiment LDS-50C-3.launch; exec bash"' \
--tab -e 'bash -c "sleep 6; roslaunch p450_experiment filter_lidar.launch; exec bash"' \

