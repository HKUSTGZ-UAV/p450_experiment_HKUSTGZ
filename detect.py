import numpy as np
import rospy
import cv2
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge, CvBridgeError
import pyrealsense2 as rs
from ultralytics import YOLO
from geometry_msgs.msg import PointStamped
import time


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
        # 订阅深度图像消息
        rospy.Subscriber("/uav1/camera/aligned_depth_to_color/image_raw", Image, self.depth_image_callback)
        # 订阅图像消息
        rospy.Subscriber("/uav1/camera/color/image_raw", Image, self.image_callback)
        # 创建一个 PointStamped 消息的发布者
        self.point_pub = rospy.Publisher('/uav/target_position', PointStamped, queue_size=10)

    def camera_to_robot_transform(self, roll=0, pitch=-3.14 * 30 / 180, yaw=0, x=0.1, y=0, z=0):
        """
        生成从相机坐标系到机器人坐标系的变换矩阵。

        参数:
        roll (float): 绕 x 轴的旋转角度（弧度）
        pitch (float): 绕 y 轴的旋转角度（弧度）
        yaw (float): 绕 z 轴的旋转角度（弧度）
        x (float): x 轴的平移量
        y (float): y 轴的平移量
        z (float): z 轴的平移量

        返回:
        np.ndarray: 4x4 的变换矩阵 T
        """
        cos_roll = np.cos(roll)
        sin_roll = np.sin(roll)
        # 绕 x 轴的旋转矩阵
        R_x = np.array([[1, 0, 0],
                      [0, cos_roll, -sin_roll],
                      [0, sin_roll, cos_roll]])
        cos_pitch = np.cos(pitch)
        sin_pitch = np.sin(pitch)
        # 绕 y 轴的旋转矩阵
        R_y = np.array([[cos_pitch, 0, sin_pitch],
                      [0, 1, 0],
                      [-sin_pitch, 0, cos_pitch]])
        cos_yaw = np.cos(yaw)
        sin_yaw = np.sin(yaw)
        # 绕 z 轴的旋转矩阵
        R_z = np.array([[cos_yaw, -sin_yaw, 0],
                      [sin_yaw, cos_yaw, 0],
                      [0, 0, 1]])
        # 计算组合旋转矩阵
        R = np.dot(np.dot(R_z, R_y), R_x)
        t = np.array([x, y, z])
        T = np.identity(4)
        T[:3, :3] = R
        T[:3, 3] = t
        return T

    def transform_point(self, T, point):
        """
        将点从相机坐标系转换到机器人坐标系。

        参数:
        T (np.ndarray): 变换矩阵
        point (np.ndarray): 输入的 3D 点（相机坐标系）

        返回:
        np.ndarray: 转换后的 3D 点（机器人坐标系）
        """
        # 将 3D 点扩展为齐次坐标
        point_homogeneous = np.append(point, 1)
        # 进行坐标变换
        transformed_point_homogeneous = np.dot(T, point_homogeneous)
        # 转换回 3D 坐标
        transformed_point = transformed_point_homogeneous[:3]
        return transformed_point

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
                # 获取边界框的坐标
                x1, y1, x2, y2 = [int(x) for x in box.xyxy[0].tolist()]
                # 计算矩形框的中心点坐标
                center_points.append(((x1 + x2) // 2, (y1 + y2) // 2))
                if show_image:
                    class_id = int(box.cls[0])
                    label = result.names[class_id]
                    confidence = box.conf[0]  # 获取置信度
                    confidence_text = "{:.2f}".format(confidence)  # 格式化置信度为两位小数
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                    # 在标签下方添加置信度文本
                    cv2.putText(frame, confidence_text, (x1, y1 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                    cv2.imshow("Detect Image", frame)
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
                    return
                # 将 2D 图像坐标转换为 3D 相机坐标
                point_camera = np.array([(x - self.camera_intrinsics[0]) * depth / self.camera_intrinsics[2],
                                         (y - self.camera_intrinsics[1]) * depth / self.camera_intrinsics[3],
                                         depth])
                print("Point in camera coordinates:", point_camera)
                a, b, c = point_camera
                point_camera = np.array([c, a, b])                
                # 转换到机器人坐标系
                T = self.camera_to_robot_transform()
                point_robot = self.transform_point(T, point_camera)
                print("Point in robot coordinates:", point_robot)
                point_stamped = PointStamped()
                point_stamped.header.stamp = rospy.Time.now()
                point_stamped.header.frame_id = 'base_link'
                point_stamped.point.x = point_robot[0] * 0.001
                point_stamped.point.y = -point_robot[1] * 0.001
                point_stamped.point.z = point_robot[2] * 0.001
                
                # 发布消息
                self.point_pub.publish(point_stamped)
                self.flag = False

    def run(self):
        # 保持节点运行
        rospy.spin()


if __name__ == "__main__":
    # roslaunch realsense2_camera rs_camera.launch
    model_name = "box.engine"
    # model_name = "best.pt"
    detector = ImageDetector(model_name, False)
    detector.run()

    # model = YOLO("best.pt")
    # model.export(format="engine")  # creates 'best.engine'
    # trt_model = YOLO("best.engine")