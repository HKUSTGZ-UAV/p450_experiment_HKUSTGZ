gnome-terminal --window -e 'bash -c "source ~/.bashrc; roslaunch p450_experiment rs_t265.launch; exec bash"' \
--tab -e 'bash -c "sleep 3; source ~/.bashrc; roslaunch p450_experiment P450_indoor_onboard.launch; exec bash"' \
