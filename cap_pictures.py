#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import os
import time
import signal
import sys

class ImageSaver:
    def __init__(self):
        rospy.init_node("realsense_image_saver", anonymous=True)
        self.bridge = CvBridge()
        self.image_sub = rospy.Subscriber("/uav1/camera/color/image_raw", Image, self.image_callback)
        self.save_path = os.path.expanduser("~/capture")
        os.makedirs(self.save_path, exist_ok=True)
        self.last_save_time = time.time()
        self.interval = 0.5  # seconds
        self.image_count = 0

        # 注册中断信号处理函数
        signal.signal(signal.SIGINT, self.shutdown_handler)
        signal.signal(signal.SIGTERM, self.shutdown_handler)

        rospy.loginfo("📷 ImageSaver node started. Press Ctrl+C to stop.")

    def image_callback(self, msg):
        now = time.time()
        if now - self.last_save_time >= self.interval:
            try:
                cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
                filename = os.path.join(self.save_path, f"frame{self.image_count:04d}.jpg")
                cv2.imwrite(filename, cv_image)
                rospy.loginfo(f"✅ Saved image: {filename}")
                self.last_save_time = now
                self.image_count += 1
            except Exception as e:
                rospy.logerr(f"❌ Failed to save image: {e}")

    def shutdown_handler(self, signum, frame):
        rospy.loginfo(f"\n🛑 Received interrupt (signal {signum}).")
        rospy.loginfo(f"📁 Total images saved: {self.image_count}")
        sys.exit(0)

    def run(self):
        rospy.spin()

if __name__ == "__main__":
    saver = ImageSaver()
    saver.run()
