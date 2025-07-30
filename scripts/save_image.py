import numpy as np
import rospy
import cv2
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import datetime


def show_image(image_name, image):
    cv2.imshow(image_name, image)
    cv2.waitKey(1)


# 创建一个 CvBridge 实例
bridge = CvBridge()
last_save_time = None


# 定义一个回调函数来处理接收到的图像消息
def image_callback(msg):
    global last_save_time
    cv_image = bridge.imgmsg_to_cv2(msg, "bgr8")
    current_time = datetime.datetime.now()
    if last_save_time is None or (current_time - last_save_time).total_seconds() >= 1:
        current_time_str = current_time.strftime("%Y%m%d_%H%M%S")
        file_name = f"/home/amov/Pictures/box_images/image_{current_time_str}.jpg"
        cv2.imwrite(file_name, cv_image)
        last_save_time = current_time
    # 显示结果
    show_image("Detected", cv_image)


# 初始化 ROS 节点
rospy.init_node('image_listener', anonymous=True)

# 创建一个 ROS 订阅者来接收图像消息
rospy.Subscriber("/uav1/camera/color/image_raw", Image, image_callback)

# 阻塞调用，直到节点被关闭
rospy.spin()