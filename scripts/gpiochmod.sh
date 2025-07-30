chmod 777 /sys/class/gpio/export
echo 492 > /sys/class/gpio/export   
chmod 777 /sys/class/gpio/PAC.06/direction
echo out > /sys/class/gpio/PAC.06/direction
chmod 777 /sys/class/gpio/PAC.06/value
# echo 1 > /sys/class/gpio/PAC.06/value