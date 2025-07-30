import numpy as np
import rospy
import cv2
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge, CvBridgeError
import pyrealsense2 as rs
from ultralytics import YOLO
from geometry_msgs.msg import PointStamped
import tf2_ros
import tf2_geometry_msgs
import time

def HSV_judge(roi, min_coutour_area=2000, kernal_size=5):
    COLOR_LOWER = np.array([75, 90, 90])
    COLOR_UPPER = np.array([100, 255, 255])
    if roi.size == 0:
        return 0, 0, 0, 0

    hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_roi, COLOR_LOWER, COLOR_UPPER)
    kernel = np.ones((kernal_size, kernal_size), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    max_area = min_coutour_area
    max_contour = None
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > max_area:
            max_area = area
            max_contour = contour
    if max_contour is not None:
        x, y, w, h = cv2.boundingRect(max_contour)
        return True, x, y, w, h
    else:
        return False, 0, 0, 0, 0

class ImageDetector:
    def __init__(self, model_name, show_image=False):
        self.show_image_flag = show_image
        # 创建 CvBridge 实例，用于图像消息转换
        self.bridge = CvBridge()
        self.camera_intrinsics = None
        self.depth_image = None
        self.depth_image_stamp = None
        self.image_stamp = None
        # 初始化 YOLO 模型
        self.model = YOLO(model_name)
        self.flag = True
        self.init_ros()
        self.get_camera_info()

    def init_ros(self):
        rospy.init_node('image_detector', anonymous=True)
        
        # 初始化 TF2
        self.tf_buffer = tf2_ros.Buffer(rospy.Duration(10.0))
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)
        
        # 订阅深度图像消息
        rospy.Subscriber("/uav1/camera/aligned_depth_to_color/image_raw", Image, self.depth_image_callback)
        # 订阅图像消息
        rospy.Subscriber("/uav1/camera/color/image_raw", Image, self.image_callback)
        # 创建一个 PointStamped 消息的发布者
        self.point_pub = rospy.Publisher('/uav/target_position', PointStamped, queue_size=10)

    def get_camera_info(self):
        """
        处理接收到的相机内参消息，存储相机内参信息。
        参数:
        camera_info_msg (sensor_msgs.msg.CameraInfo): 相机内参消息
        """
        while self.camera_intrinsics is None:
            camera_info_msg = rospy.wait_for_message("/uav1/camera/aligned_depth_to_color/camera_info", CameraInfo, timeout=5.0)
            if camera_info_msg is not None:
                self.camera_intrinsics = np.array([
                    camera_info_msg.K[2],
                    camera_info_msg.K[5],
                    camera_info_msg.K[0],
                    camera_info_msg.K[4]
                ])
                print("Received camera intrinsics")
                print("Camera intrinsics:", self.camera_intrinsics)

    def depth_image_callback(self, depth_image_msg):
        """
        处理接收到的深度图像消息，将其转换为 OpenCV 图像。

        参数:
        depth_image_msg (sensor_msgs.msg.Image): 深度图像消息
        """
        self.depth_image_stamp = depth_image_msg.header.stamp
        self.depth_image = self.bridge.imgmsg_to_cv2(depth_image_msg, desired_encoding="passthrough")
    
    def yolo_detect(self, frame, show_image=False):
        """
        使用 YOLO 模型对输入图像进行目标检测，并绘制检测框，同时输出矩形框中心点坐标。

        参数:
        frame (np.ndarray): 输入的图像帧
        model: YOLO 模型

        返回:
        list: 矩形框中心点坐标列表
        """
        # 进行目标检测
        results = self.model(frame, verbose=False)
        center_points = []
        for result in results:
            for box in result.boxes:
                # 先拿置信度，低于 0.9 的直接跳过
                confidence = box.conf[0].item() if hasattr(box.conf[0], 'item') else float(box.conf[0])
                if confidence < 0.85:
                    continue
                # 获取边界框的坐标
                x1, y1, x2, y2 = [int(x) for x in box.xyxy[0].tolist()]
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                # 计算矩形框的中心点坐标
                roi = frame[y1:y2, x1:x2]
                is_box, x, y, w, h = HSV_judge(roi)
                if not is_box:
                    continue
                x1, y1, x2, y2 = x1 + x, y1 + y, x1 + x + w, y1 + y + h
                center_points.append(((x1 + x2) // 2, (y1 + y2) // 2))
                
                class_id = int(box.cls[0])
                label = result.names[class_id]
                confidence = box.conf[0]  # 获取置信度
                confidence_text = "{:.2f}".format(confidence)  # 格式化置信度为两位小数
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                # 在标签下方添加置信度文本
                cv2.putText(frame, confidence_text, (x1, y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
        if show_image:
            resized_frame = cv2.resize(frame, (frame.shape[1] // 2, frame.shape[0] // 2))
            cv2.imshow("Detect Image", resized_frame)
            cv2.waitKey(1)
                
        return center_points

    def hough_detect(self, frame):
        """
        对输入的图像进行霍夫圆检测，返回检测到的圆的中心坐标。

        参数:
        frame (np.ndarray): 输入图像

        返回:
        list: 圆的中心坐标列表
        """
        # 转换为灰度图像
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # 高斯模糊处理
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        # 霍夫圆检测
        circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=50,
                               param1=200, param2=200, minRadius=10, maxRadius=1000000)
        circle_centers = []
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            for (x, y, _) in circles:
                circle_centers.append((x, y))
        return circle_centers

    def image_callback(self, image_msg):
        """
        处理接收到的图像消息，进行圆检测，将检测到的圆心从 2D 转换为 3D 相机坐标，再转换为机器人坐标。

        参数:
        image_msg (sensor_msgs.msg.Image): 图像消息
        """
        if not self.flag:
            return
        self.image_stamp = image_msg.header.stamp
        # if not self.image_stamp or not self.depth_image_stamp or (self.image_stamp - self.depth_image_stamp).to_sec() > 0.1:
        #     return
        cv_image = self.bridge.imgmsg_to_cv2(image_msg, "bgr8")
        circle_centers = self.yolo_detect(cv_image, self.show_image_flag)
        if self.depth_image is not None and self.camera_intrinsics is not None:
            for x, y in circle_centers:
                # 获取深度信息
                depth = self.depth_image[y, x]
                if depth < 10 or depth > 10000:
                    # rospy.logwarn(f"Invalid depth value: {depth} at pixel ({x}, {y})")
                    continue
                
                # 反投影到相机光学坐标系，不做手动轴重排
                Xc = (x - self.camera_intrinsics[0]) * depth / self.camera_intrinsics[2]
                Yc = (y - self.camera_intrinsics[1]) * depth / self.camera_intrinsics[3]
                Zc = depth
                
                print("Point in camera coordinates:", [Xc, Yc, Zc])
                
                # 使用 TF2 进行坐标变换，替代手动计算
                pt_cam = PointStamped()
                # pt_cam.header.frame_id = 'uav1/camera_link'
                pt_cam.header.frame_id = 'uav1/camera_color_optical_frame'
                pt_cam.header.stamp = self.depth_image_stamp  # 使用深度帧时间戳
                pt_cam.point.x = Xc * 0.001  # 转换为米
                pt_cam.point.y = Yc * 0.001
                pt_cam.point.z = Zc * 0.001
                
                try:
                    # 从 camera_link → base_link 做变换
                    trans = self.tf_buffer.lookup_transform(
                        'base_link_frd',                           # 机体 frame
                        'uav1/camera_aligned_depth_to_color_frame',# 对齐深度到彩色后的相机 frame
                        pt_cam.header.stamp,        # 对齐深度帧时间戳
                        rospy.Duration(0.1))        # 最多等 0.1s
                except (tf2_ros.LookupException,
                        tf2_ros.ExtrapolationException,
                        tf2_ros.ConnectivityException) as e:
                    rospy.logwarn(f'TF lookup failed: {e}')
                    continue   # 如果没拿到就跳过这个点

                # 真正做坐标变换
                # pt_body = tf2_geometry_msgs.do_transform_point(pt_cam, trans)
                # 直接从 optical → base_link_frd
                pt_body = self.tf_buffer.transform(
                    pt_cam,
                    'base_link_frd',
                    # 'uav1/base_link',  # 直接从 optical → base_link
                    rospy.Duration(0.1))

                # 拿到机体坐标系下的点
                x_b = pt_body.point.x
                y_b = -pt_body.point.y
                z_b = -pt_body.point.z

                # 打印检查
                rospy.loginfo(f'Point in base_link: [{x_b:.3f}, {y_b:.3f}, {z_b:.3f}]')

                # 发布给控制器
                target_msg = PointStamped()
                target_msg.header.stamp = rospy.Time.now()
                target_msg.header.frame_id = 'uav1/base_link'
                target_msg.point.x = x_b
                target_msg.point.y = y_b
                target_msg.point.z = z_b
                self.point_pub.publish(target_msg)
    def run(self):
        rospy.spin()

if __name__ == '__main__':
    # 参数: 模型路径，可选是否显示图片
    # model_path = rospy.get_param('~model_path', 'best.pt')
    model_path = rospy.get_param('~model_path', 'box.pt')
    # show_img   = rospy.get_param('~show_image', False)
    show_img = rospy.get_param('~show_image', True)
    detector = ImageDetector(model_path, show_img)
    detector.run()
