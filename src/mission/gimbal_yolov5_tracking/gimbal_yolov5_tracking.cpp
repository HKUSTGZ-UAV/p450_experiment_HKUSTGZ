#include <ros/ros.h>
#include <sstream>
#include <Eigen/Eigen>
#include <iostream>
#include <prometheus_msgs/UAVState.h>
#include <prometheus_msgs/UAVCommand.h>
#include <prometheus_msgs/UAVControlState.h>
#include <spirecv_msgs/TargetsInFrame.h>
#include <spirecv_msgs/Target.h>
#include <spirecv_msgs/ROI.h>
#include <spirecv_msgs/GimbalState.h>
#include <mission_utils.h>
#include "printf_utils.h"

using namespace std;
using namespace Eigen;
#define NODE_NAME "gimbal_yolov5_tracking"
prometheus_msgs::UAVState g_UAVState;
Eigen::Vector3f g_drone_pos;
float height;
prometheus_msgs::UAVControlState g_uavcontrol_state;
spirecv_msgs::Target g_Detection_raw;      //目标位置[机体系下：前方x为正，右方y为正，下方z为正]
spirecv_msgs::TargetsInFrame det;
prometheus_msgs::UAVCommand g_command_now; //发送给控制模块的命令
int g_uav_id;

float kpx_track, kpy_track, kpz_track; //控制参数 - 比例参数
bool is_detected = false;              // 是否检测到目标标志
float gimbal_roll, gimbal_pitch, gimbal_yaw; //吊舱RYP参数
spirecv_msgs::GimbalState g_GimbalState;

void droneStateCb(const prometheus_msgs::UAVState::ConstPtr &msg)
{
    g_UAVState = *msg;
    g_drone_pos[0] = g_UAVState.position[0];
    g_drone_pos[1] = g_UAVState.position[1];
    g_drone_pos[2] = g_UAVState.position[2];
    height = g_UAVState.rel_alt;
}

void VisionCb(const spirecv_msgs::TargetsInFrame::ConstPtr &msg)
{
    det = *msg;
    // car_id = det.frame_id;
    g_Detection_raw.mode = false;
    for(auto &tar : msg->targets)
    {
        g_Detection_raw = tar;
    }
}

void GimbalStateCb(const spirecv_msgs::GimbalState::ConstPtr &msg)
{
    g_GimbalState = *msg;
    gimbal_roll = g_GimbalState.angleRT[0];
    gimbal_pitch = g_GimbalState.angleRT[1];
    gimbal_yaw = g_GimbalState.angleRT[2];
}

void droneControlStateCb(const prometheus_msgs::UAVControlState::ConstPtr &msg)
{
    g_uavcontrol_state = *msg;
}

inline float clamp(float value, float max)
{
    max = std::abs(max);
    return std::fmin(std::fmax(value,-max),max);
}

int main(int argc, char **argv)
{
    ros::init(argc,argv,"gimbal_yolov5_tracking");
    ros::NodeHandle nh;
    
    float kp_x, kp_z, kp_gimbal, max_velocity, max_yaw_rate, expect_height;
    nh.param<float>(ros::this_node::getName() + "/kp_x", kp_x, 1);
    nh.param<float>(ros::this_node::getName() + "/kp_z", kp_z, 0.005);
    nh.param<float>(ros::this_node::getName() + "/kp_gimbal", kp_gimbal, 0.01);
    nh.param<float>(ros::this_node::getName() + "/max_velocity", max_velocity, 1);
    nh.param<float>(ros::this_node::getName() + "/max_yaw_rate", max_yaw_rate, 10);
    nh.param<int>(ros::this_node::getName() + "uav_id", g_uav_id, 1);
    
    //获取无人机ENU下位置
    ros::Subscriber curr_pos_sub = nh.subscribe<prometheus_msgs::UAVState>("/uav" + std::to_string(g_uav_id) + "/prometheus/state", 10, droneStateCb);
    //获取遥控器控制状态
    ros::Subscriber uav_control_state_sub = nh.subscribe<prometheus_msgs::UAVControlState>("/uav" + std::to_string(g_uav_id) + "/prometheus/control_state", 10, droneControlStateCb);
    //获取吊舱状态
    ros::Subscriber gimbal_state_sub = nh.subscribe<spirecv_msgs::GimbalState>("/uav" + std::to_string(g_uav_id) + "/gimbal/state", 10, GimbalStateCb);
    //获取视觉反馈
    ros::Subscriber vision_sub = nh.subscribe<spirecv_msgs::TargetsInFrame>("/uav" + std::to_string(g_uav_id) + "/spirecv/target", 10, VisionCb);
    //发布控制指令到uav_controller
    ros::Publisher command_pub = nh.advertise<prometheus_msgs::UAVCommand>("/uav" + std::to_string(g_uav_id) + "/prometheus/command", 10);
   

    ros::Rate rate(25);
    while(ros::ok())
    {
        ros::spinOnce();
        if(g_uavcontrol_state.control_state != prometheus_msgs::UAVControlState::COMMAND_CONTROL)
        {
            PCOUT(-1, WHITE, "Waiting for enter COMMAND_CONTROL state");
            expect_height = height;
        }
        if(!g_Detection_raw.mode || g_GimbalState.moveMode != 3)
        {
            g_command_now.Agent_CMD = prometheus_msgs::UAVCommand::Current_Pos_Hover;
            PCOUT(-1, GREEN, "Waiting for click target && gimbal track");
        }
        else
        {
            g_command_now.Agent_CMD = prometheus_msgs::UAVCommand::Move;
            g_command_now.Move_mode = prometheus_msgs::UAVCommand::XYZ_VEL_BODY;
            g_command_now.Yaw_Rate_Mode = true;
            float x_vel;
            float y_vel = 0;
            float z_vel = 0;//kp_z * (expect_height - g_drone_pos[2]);
            //float yaw_rate = -kp_gimbal * gimbal_yaw;
            float yaw_rate;
            if(gimbal_yaw > -80 && gimbal_yaw < -3)
            {
            	x_vel = 0;
            	yaw_rate = -kp_gimbal * gimbal_yaw;
            }else if(gimbal_yaw > 3 && gimbal_yaw < 80)
            {
            	x_vel = 0;
            	yaw_rate = -kp_gimbal * gimbal_yaw;
            }else
            {
            	x_vel = kp_x * (g_Detection_raw.pz - 2.0);
            	yaw_rate = 0;
            }
            g_command_now.velocity_ref[0] = clamp(x_vel, max_velocity);
            g_command_now.velocity_ref[1] = 0;
            g_command_now.velocity_ref[2] = 0;
            g_command_now.yaw_rate_ref = clamp(yaw_rate, max_yaw_rate) * M_PI / 180;
            PCOUT(-1, GREEN, "target tracking!");
        }
        // Publish
        g_command_now.header.stamp = ros::Time::now();
        g_command_now.Command_ID = g_command_now.Command_ID + 1;
        if (g_command_now.Command_ID < 10)
            g_command_now.Agent_CMD = prometheus_msgs::UAVCommand::Init_Pos_Hover;
        command_pub.publish(g_command_now);
        rate.sleep();
    }
    return 0;
}
