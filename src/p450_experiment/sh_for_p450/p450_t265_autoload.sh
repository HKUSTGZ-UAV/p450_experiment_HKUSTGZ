# 用于驱动T265-USB3.0接口，相当于插拔一次
gnome-terminal --window -e 'bash -c "EnableGpio_for_USB.sh"' \
--tab -e 'bash -c "sleep 3;EnableGpio_for_USB.sh"' \

# 启动通信节点
gnome-terminal --window -e 'bash -c "source /opt/ros/noetic/setup.bash && source ~/p450_experiment/devel/setup.bash && roslaunch p450_experiment p450_t265_communication.launch; exec bash"' \
