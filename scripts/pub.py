#!/usr/bin/env python
# coding: utf-8

import rospy
from geometry_msgs.msg import PointStamped
import random
import math

def publish_target_position():
    rospy.init_node('publish_target_position', anonymous=True)
    target_pub = rospy.Publisher('/uav/target_position', PointStamped, queue_size=10)
    rate = rospy.Rate(0.1)  # 0.1 Hz

    while not rospy.is_shutdown():
        target_msg = PointStamped()
        target_msg.header.stamp = rospy.Time.now()
        target_msg.point.x = random.uniform(-5.0, 5.0)
        target_msg.point.y = random.uniform(-5.0, 5.0)
        # target_msg.point.x = 1.0
        # target_msg.point.y = 1.0
        target_msg.point.z = 1.5  # Assuming 2D movement

        rospy.loginfo("Publishing target position: x=%f, y=%f, z=%f", target_msg.point.x, target_msg.point.y, target_msg.point.z)
        target_pub.publish(target_msg)
        rate.sleep()


def publish_target_position_circle():
    rospy.init_node('publish_target_position', anonymous=True)
    target_pub = rospy.Publisher('/uav/target_position', PointStamped, queue_size=10)
    rate = rospy.Rate(10)  # 10 Hz 更新更平滑

    radius = 0.5           # 圆的半径
    center_x = 0.0          # 圆心 X 坐标
    center_y = 0.0          # 圆心 Y 坐标
    angular_speed = 0.2     # 每秒弧度（约0.2 rad/s ≈ 1圈32秒）

    theta = 0.0             # 初始角度

    while not rospy.is_shutdown():
        target_msg = PointStamped()
        target_msg.header.stamp = rospy.Time.now()

        # 沿圆轨迹生成目标点
        target_msg.point.x = center_x + radius * math.cos(theta)
        target_msg.point.y = center_y + radius * math.sin(theta)
        target_msg.point.z = 1.5  # 固定高度

        rospy.loginfo("Circular target: x=%.2f, y=%.2f, z=%.2f", 
                      target_msg.point.x, target_msg.point.y, target_msg.point.z)

        target_pub.publish(target_msg)

        theta += angular_speed / 10.0  # 每次循环更新角度（10Hz）
        if theta >= 2 * math.pi:
            theta -= 2 * math.pi  # 保证在 [0, 2π] 范围循环

        rate.sleep()

def publish_manual_target():
    rospy.init_node('manual_target_input', anonymous=True)
    target_pub = rospy.Publisher('/uav/target_position', PointStamped, queue_size=10)
    rate = rospy.Rate(1)

    print("\n🛫 UAV 手动目标点发布器已启动！")
    print("输入格式：x y z，例如 `1.0 2.0 1.5`")
    print("输入 q 或 Ctrl+C 退出\n")

    while not rospy.is_shutdown():
        try:
            user_input = input("请输入目标点坐标 (x y z)：")
            if user_input.lower() in ['q', 'quit', 'exit']:
                print("✅ 退出程序。")
                break

            parts = user_input.strip().split()
            if len(parts) != 3:
                print("⚠️ 请输入三个浮点数，例如：1.0 2.0 1.5")
                continue

            x, y, z = map(float, parts)

            target_msg = PointStamped()
            target_msg.header.stamp = rospy.Time.now()
            target_msg.point.x = x
            target_msg.point.y = y
            target_msg.point.z = z

            target_pub.publish(target_msg)
            rospy.loginfo("📡 已发布目标点: x=%.2f, y=%.2f, z=%.2f", x, y, z)

        except ValueError:
            print("❌ 输入非法，请重新输入三个数值")
        except KeyboardInterrupt:
            print("\n🛑 手动终止。")
            break

        rate.sleep()

if __name__ == '__main__':
    try:
        # publish_target_position()
        # publish_target_position_circle()
        publish_manual_target()
    except rospy.ROSInterruptException:
        pass
    except KeyboardInterrupt:
        rospy.signal_shutdown("KeyboardInterrupt")