#include <ros/ros.h>
#include <prometheus_msgs/UAVCommand.h>
#include <prometheus_msgs/UAVState.h>
#include <prometheus_msgs/UAVControlState.h>
#include <geometry_msgs/PointStamped.h>
#include <unistd.h>
#include <Eigen/Eigen>
#include "printf_utils.h"
#include <fstream>  // For file operations
#include <iomanip>  // For setw, setfill
#include <chrono>   // For high precision timestamps
#include <ctime>    // For time formatting
#include <signal.h> // For signal handling

using namespace std;

// File for logging
ofstream logFile;

// Function to get current timestamp in milliseconds precision
string getTimestamp() {
    auto now = chrono::system_clock::now();
    auto now_time_t = chrono::system_clock::to_time_t(now);
    auto now_ms = chrono::duration_cast<chrono::milliseconds>(now.time_since_epoch()) % 1000;
    
    struct tm now_tm;
    localtime_r(&now_time_t, &now_tm);
    
    stringstream ss;
    ss << put_time(&now_tm, "%Y-%m-%d %H:%M:%S") << '.' 
       << setfill('0') << setw(3) << now_ms.count();
    return ss.str();
}

// Function to write logs to file while preserving original console output
void writeLog(const string& message, const string& color = "") {
    string timestamp = getTimestamp();
    
    // Write to file
    if (logFile.is_open()) {
        logFile << timestamp << " " << message << endl;
        logFile.flush();
    }
    
    // Keep original console output behavior
    // cout << color << message << TAIL << endl;
}

// Signal handler for proper cleanup
void signalHandler(int signum) {
    if (logFile.is_open()) {
        writeLog("Program terminated by signal " + to_string(signum));
        logFile.close();
    }
    exit(signum);
}

//创建无人机相关数据变量
prometheus_msgs::UAVCommand uav_command;
prometheus_msgs::UAVState uav_state;
prometheus_msgs::UAVControlState uav_control_state;

Eigen::Vector3d target_pos_body(1.0, 0.0, 0.0); // body坐标系下的目标位置
Eigen::Vector3d tracking_delta(0.0, 0.0, 0.0);   // enu偏移，参数化配置
Eigen::Vector3d last_target_pos_enu(0.0, 0.0, 0.0); // 上一次目标位置
Eigen::Vector3d target_pos_enu(1.0, 0.0, 0.0); // enu坐标系下的目标位置
Eigen::Vector3d init_target(1.0, 0.0, 0.0); // enu坐标系下的目标位置

bool first_update = true;
bool use_vision_loss = false; // 是否使用视觉丢失处理
bool target_detected_once = false; // Flag to track if the target has ever been detected

int vision_lost_counter = 0;
int vision_regain_counter = 0;
int vision_lost_threshold = 10;
ros::Time last_target_time;

constexpr int MAX_MISSES = 5; // Maximum consecutive misses before considering the target lost
int miss_count = 0;

//无人机状态回调函数
void uav_state_cb(const prometheus_msgs::UAVState::ConstPtr &msg)
{
    uav_state = *msg;
}

//无人机控制状态回调函数
void uav_control_state_cb(const prometheus_msgs::UAVControlState::ConstPtr &msg)
{
    uav_control_state = *msg;
}

Eigen::Vector3d body_to_enu(const Eigen::Vector3d& body_pos, const Eigen::Quaterniond& orientation)
{
    return orientation * body_pos; // 使用四元数旋转
}

void target_pos_cb(const geometry_msgs::PointStamped::ConstPtr &msg)
{
    target_pos_body[0] = msg->point.x;
    target_pos_body[1] = msg->point.y;
    target_pos_body[2] = msg->point.z;
    last_target_time = ros::Time::now();

    // 只有接收到新目标时才转换一次
    Eigen::Quaterniond q_uav(
        uav_state.attitude_q.w,
        uav_state.attitude_q.x,
        uav_state.attitude_q.y,
        uav_state.attitude_q.z);
    q_uav.normalize();

    Eigen::Vector3d uav_enu_pos(
        uav_state.position[0],
        uav_state.position[1],
        uav_state.position[2]);

    Eigen::Vector3d target_body_adjusted = target_pos_body + tracking_delta;
    target_pos_enu = uav_enu_pos + q_uav * target_body_adjusted;

    target_detected_once = true; // Mark that the target has been detected at least once
}


//主函数
int main(int argc, char** argv)
{
    ros::init(argc , argv, "enu_xyz_pos_control");
    ros::NodeHandle n;
    
    // Open log file in root directory
    logFile.open("/enu_xyz_pos_control.log", ios::app);
    if (!logFile.is_open()) {
        cout << RED << "Failed to open log file!" << TAIL << endl;
    } else {
        writeLog("Log file opened successfully", GREEN);
    }
    
    // Register signal handler for proper cleanup
    signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);

    //声明起飞高度,无人机id变量
    float takeoff_height;
    int uav_id;
    //获取起飞高度参数
    ros::param::get("/uav_control_main_1/control/Takeoff_height", takeoff_height);
    ros::param::get("~uav_id", uav_id);

    // 读取 tracking_delta 参数
    n.param("tracking_delta_x", tracking_delta[0], 0.0);
    n.param("tracking_delta_y", tracking_delta[1], 0.0);
    n.param("tracking_delta_z", tracking_delta[2], 0.0);
    n.param("vision_lost_threshold", vision_lost_threshold, 10);  // 容错阈值
    
    ros::Publisher uav_command_pub = n.advertise<prometheus_msgs::UAVCommand>("/uav" + std::to_string(uav_id) + "/prometheus/command", 10);
    ros::Subscriber uav_state_sub = n.subscribe<prometheus_msgs::UAVState>("/uav" + std::to_string(uav_id) + "/prometheus/state", 10, uav_state_cb);
    ros::Subscriber uav_control_state_sub = n.subscribe<prometheus_msgs::UAVControlState>("/uav" + std::to_string(uav_id) + "/prometheus/control_state", 10, uav_control_state_cb);
    ros::Subscriber target_sub = n.subscribe<geometry_msgs::PointStamped>("/uav/target_position", 10, target_pos_cb);

    ros::Rate r(25);
    cout << GREEN << "[ENU XYZ position control] with tracking_delta and vision loss handling" << TAIL << endl;
    writeLog("[ENU XYZ position control] with tracking_delta and vision loss handling");

    cout.setf(ios::fixed);
    cout << setprecision(2);
    cout.setf(ios::left);
    cout.setf(ios::showpoint);
    cout.setf(ios::showpos);
    
    //打印demo相关信息
    cout << GREEN << " [ENU XYZ position control] tutorial_demo start " << TAIL << endl;
    writeLog("[ENU XYZ position control] tutorial_demo start");
    sleep(1);
    cout << GREEN << " Level: [Basic] " << TAIL << endl;
    writeLog("Level: [Basic]");
    sleep(1);
    cout << GREEN << " Please use the RC SWA to armed, and the SWB to switch the drone to [COMMAND_CONTROL] mode  " << TAIL << endl;
    writeLog("Please use the RC SWA to armed, and the SWB to switch the drone to [COMMAND_CONTROL] mode");
    sleep(1);
    // 配置GPIO
    system("echo 492 > /sys/class/gpio/export");
    system("echo out > /sys/class/gpio/PAC.06/direction");
    system("echo 1 > /sys/class/gpio/PAC.06/value");
    sleep(1);
    cout<<GREEN<<"gpio configured"<<TAIL<<endl;
    writeLog("gpio configured");
    
    while(ros::ok())
    {
        ros::spinOnce();

        // ===================== 控制前置检查 =====================
        if (uav_control_state.control_state != prometheus_msgs::UAVControlState::COMMAND_CONTROL)
        {
            cout << YELLOW << " Waiting for UAV to enter [COMMAND_CONTROL] MODE " << TAIL << endl;
            writeLog("Waiting for UAV to enter [COMMAND_CONTROL] MODE");
            r.sleep();
            continue;
        }

        if (fabs(uav_state.position[2] - takeoff_height) >= 0.3 || uav_state.position[2] < 0.1)
        {
            printf("takeoff height: %.2f, uav_state.position[2]: %.2f\n", takeoff_height, uav_state.position[2]);
            stringstream ss;
            ss << "takeoff height: " << fixed << setprecision(2) << takeoff_height << ", uav_state.position[2]: " << uav_state.position[2];
            writeLog(ss.str());
            
            cout << YELLOW << " Waiting for UAV to reach takeoff height..." << TAIL << endl;
            writeLog("Waiting for UAV to reach takeoff height...");
            r.sleep();
            continue;
        }

        if (use_vision_loss)
        {
            // ===================== 判断视觉是否失效 =====================
            double time_since_last_detection = (ros::Time::now() - last_target_time).toSec();
            if (time_since_last_detection > 0.5)
            {
                vision_lost_counter++;
                miss_count++;
            }
            else
            {
                vision_lost_counter = 0;
                miss_count = 0;
            }

            if (vision_lost_counter >= vision_lost_threshold || miss_count >= MAX_MISSES)
            {
                // 执行悬停
                uav_command.Agent_CMD = prometheus_msgs::UAVCommand::Current_Pos_Hover;
                uav_command.header.stamp = ros::Time::now();
                uav_command.Command_ID++;
                uav_command_pub.publish(uav_command);
                cout << RED << " Vision Lost! Holding Position." << TAIL << endl;
                writeLog("Vision Lost! Holding Position.");
                r.sleep();
                continue;
            }
        }

        Eigen::Vector3d uav_enu_pos(
            uav_state.position[0],
            uav_state.position[1],
            uav_state.position[2]);

        // 起飞成功后，每次循环都发布移动指令到最新目标位置
        uav_command.header.stamp = ros::Time::now();
        uav_command.header.frame_id = "ENU";
        uav_command.Agent_CMD = prometheus_msgs::UAVCommand::Move;
        uav_command.Move_mode = prometheus_msgs::UAVCommand::XYZ_POS;
        uav_command.position_ref[0] = target_pos_enu[0];
        uav_command.position_ref[1] = target_pos_enu[1];
        uav_command.position_ref[2] = takeoff_height;
        // 设置速度
        uav_command.velocity_ref[0] = 0.5;
        uav_command.velocity_ref[1] = 0.5;
        uav_command.velocity_ref[2] = 0.5;
        // 设置加速度
        // uav_command.acceleration_ref[0] = 0.01;
        // uav_command.acceleration_ref[1] = 0.01;
        // uav_command.acceleration_ref[2] = 0.01;

        uav_command.yaw_ref = 0.0;
        uav_command.Command_ID += 1;
        uav_command_pub.publish(uav_command);

        cout << GREEN << " Tracking target at (ENU): " << target_pos_enu.transpose() << TAIL << endl;
        stringstream ss1;
        ss1 << "Tracking target at (ENU): " << target_pos_enu.transpose();
        writeLog(ss1.str());
        
        cout << GREEN << " Tracking target at (BODY): " << target_pos_body.transpose() << TAIL << endl;
        stringstream ss2;
        ss2 << "Tracking target at (BODY): " << target_pos_body.transpose();
        writeLog(ss2.str());

        // 计算无人机当前位置与目标点的距离
        // float distance = (uav_enu_pos - target_pos_enu).norm();
        // 只算xy平面距离
        float distance = sqrt(pow(uav_enu_pos[0] - target_pos_enu[0], 2) + pow(uav_enu_pos[1] - target_pos_enu[1], 2));

        if (first_update)
        {
            last_target_pos_enu = target_pos_enu;
            first_update = false;
        }
        // 判断target是否和init_target相同,bool,
        // bool target_stable = (target_pos_enu - init_target).norm() < 0.01;


        float target_change = (target_pos_enu - last_target_pos_enu).norm();
        static bool drop_executed = false;

        // 打印 distance 和 target_change
        printf("distance: %.2f, target_change: %.2f\n", distance, target_change);
        stringstream ss3;
        ss3 << "distance: " << fixed << setprecision(2) << distance << ", target_change: " << target_change;
        writeLog(ss3.str());

        // 投掷后保持悬停
        if (distance <= 0.1 && target_change <= 0.2 && !drop_executed)
        {
            if (!target_detected_once)
            {
                cout << RED << " Target has never been detected. Aborting drop." << TAIL << endl;
                writeLog("Target has never been detected. Aborting drop.");
                continue;
            }

            // 向下降低0.2m
            // uav_command.Agent_CMD = prometheus_msgs::UAVCommand::Move;
            // uav_command.Move_mode = prometheus_msgs::UAVCommand::XYZ_POS;
            // uav_command.position_ref[0] = target_pos_enu[0];
            // uav_command.position_ref[1] = target_pos_enu[1];
            // uav_command.position_ref[2] = takeoff_height - 0.2; // 降低0.2m
            // uav_command.velocity_ref[0] = 0.1;
            // uav_command.velocity_ref[1] = 0.1;
            // uav_command.velocity_ref[2] = 0.1;
            // uav_command.yaw_ref = 0.0;
            // uav_command.Command_ID++;
            // uav_command_pub.publish(uav_command);
            // cout << YELLOW << " UAV descending to drop payload." << TAIL << endl;

            // 模拟投掷操作
            system("echo 0 > /sys/class/gpio/PAC.06/value");
            drop_executed = true;
            cout << YELLOW << " UAV reached target and target stable. Dropping payload." << TAIL << endl;
            writeLog("UAV reached target and target stable. Dropping payload.");

            // 设置当前 ENU 位置为新的静止 hover 点
            uav_command.Agent_CMD = prometheus_msgs::UAVCommand::Current_Pos_Hover;
            uav_command.header.stamp = ros::Time::now();
            uav_command.Command_ID++;
            uav_command_pub.publish(uav_command);
            
            cout << YELLOW << " UAV entering hold mode after drop." << TAIL << endl;
            writeLog("UAV entering hold mode after drop.");

            while (ros::ok())
            {
                ros::spinOnce();
                uav_command.Agent_CMD = prometheus_msgs::UAVCommand::Current_Pos_Hover;
                uav_command.header.stamp = ros::Time::now();
                uav_command.Command_ID++;
                uav_command_pub.publish(uav_command);
                cout << RED << " UAV holding position after drop." << TAIL << endl;
                writeLog("UAV holding position after drop.");
                r.sleep();
            }
        }

        // 更新上一次目标位置
        last_target_pos_enu = target_pos_enu;
        r.sleep();
    }

    // Close log file properly
    if (logFile.is_open()) {
        writeLog("Program terminated normally");
        logFile.close();
    }

    return 0;
}