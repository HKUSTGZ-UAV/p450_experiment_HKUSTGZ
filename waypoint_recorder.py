#!/usr/bin/env python3
import rospy
from geometry_msgs.msg import PoseStamped
import json
import os
import signal
import sys

waypoints = []

def callback(msg):
    p = msg.pose.position
    waypoints.append({'x': p.x, 'y': p.y, 'z': p.z})
    rospy.loginfo(f"📍 Added waypoint: {p.x:.2f}, {p.y:.2f}, {p.z:.2f}")

def save_and_exit(signum, frame):
    output_path = os.path.expanduser('~/maps/warehouse_waypoints.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(waypoints, f, indent=2)
    rospy.loginfo(f"\n✅ Saved {len(waypoints)} waypoints to {output_path}")
    sys.exit(0)

if __name__ == '__main__':
    rospy.init_node('waypoint_recorder')
    signal.signal(signal.SIGINT, save_and_exit)

    # 关键订阅正确的话题
    rospy.Subscriber('/uav1/prometheus/motion_planning/goal', PoseStamped, callback)

    rospy.loginfo("🎯 Click Nav Goals in RViz. Ctrl+C to save & exit.")
    rospy.spin()
