#include "ros/ros.h"
#include "std_msgs/Int16.h"
#include <nav_msgs/Odometry.h>
#include <geometry_msgs/PoseStamped.h>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2_ros/transform_broadcaster.h>
#include <cmath>
#include <geometry_msgs/Vector3.h>
#include <stdio.h>
#include <tf/transform_broadcaster.h>



double rate = 10.0;
double linear_scale_positive = 1.0;
double linear_scale_negative = 1.0;
double angular_scale_positive = 1.0;
double angular_scale_negative = 1.0;
bool publish_tf = true;
double dt = 0.0;
double dx = 0.0;
double dy = 0.0;
double dth = 0.0;
double dxy = 0.0;
double vx = 0.0;
double vy = 0.0;
double vth = 0.0;
double cycleAngle = 0.0;
bool initialPoseRecieved = false;
const double initialX = 0.0;
const double initialY = 0.0;
const double initialTheta = 0.00000000001;
const double PI = 3.141592;
double radius = 0.05;                              //Wheel radius, in m
double wheelbase = 0.33;                          //Wheelbase, in m
double two_pi = 6.28319;
double speed_act_left = 0.0;
double speed_act_right = 0.0;
double speed_req1 = 0.0;
double speed_req2 = 0.0;
double speed_dt = 0.0;
double x_pos = 0.0;
double y_pos = 0.0;
double theta = 0.0;
char base_link[] = "/base_link";
char odom[] = "/odom";
ros::Time current_time;
ros::Time speed_time(0.0);

ros::Publisher odom_data_pub;
ros::Publisher odom_data_pub_quat;
nav_msgs::Odometry odomOld;
nav_msgs::Odometry odom_msg;


// Distance both wheels have traveled
double distanceLeft = 0;
double distanceRight = 0;


using namespace std;

// Get initial_2d message from either Rviz clicks or a manual pose publisher
void set_initial_2d(const geometry_msgs::PoseStamped &rvizClick) {
 
  odomOld.pose.pose.position.x = rvizClick.pose.position.x;
  odomOld.pose.pose.position.y = rvizClick.pose.position.y;
  odomOld.pose.pose.orientation.z = rvizClick.pose.orientation.z;
  initialPoseRecieved = true;
}

void publish_quat()
{
    tf2::Quaternion q;
    q.setRPY(0, 0, odom_msg.pose.pose.orientation.z);
    nav_msgs::Odometry quatOdom;
    quatOdom.header.stamp = odom_msg.header.stamp;
    quatOdom.header.frame_id = "odom";
    quatOdom.child_frame_id = "base_link";
    quatOdom.pose.pose.position.x = odom_msg.pose.pose.position.x;
    quatOdom.pose.pose.position.y = odom_msg.pose.pose.position.y;
    quatOdom.pose.pose.position.z = odom_msg.pose.pose.position.z;
    quatOdom.pose.pose.orientation.x = q.x();
    quatOdom.pose.pose.orientation.y = q.y();
    quatOdom.pose.pose.orientation.z = q.z();
    quatOdom.pose.pose.orientation.w = q.w();
    quatOdom.twist.twist.linear.x = odom_msg.twist.twist.linear.x;
    quatOdom.twist.twist.linear.y = odom_msg.twist.twist.linear.y;
    quatOdom.twist.twist.linear.z = odom_msg.twist.twist.linear.z;
    quatOdom.twist.twist.angular.x = odom_msg.twist.twist.angular.x;
    quatOdom.twist.twist.angular.y = odom_msg.twist.twist.angular.y;
    quatOdom.twist.twist.angular.z = odom_msg.twist.twist.angular.z;
 
    for(int i = 0; i<36; i++) {
      if(i == 0 || i == 7 || i == 14) {
        quatOdom.pose.covariance[i] = .01;
       }
       else if (i == 21 || i == 28 || i== 35) {
        quatOdom.pose.covariance[i] += 0.1;
       }
       else {
         quatOdom.pose.covariance[i] = 0;
       }
    }
 
    odom_data_pub_quat.publish(quatOdom);
}

void update_odom() 
{
    ros::spinOnce();
    current_time = speed_time;
    dt = speed_dt;					//Time in s
    ROS_INFO("dt : %f", dt);
    dxy = (speed_act_left+speed_act_right)*dt/2;
    cycleAngle = asin((speed_act_right-speed_act_left)*dt/wheelbase);
    ROS_INFO("dxy : %f", dxy);
    dth = ((speed_act_right-speed_act_left)*dt)/wheelbase;
    
    if (dth > 0) dth *= angular_scale_positive;
    if (dth < 0) dth *= angular_scale_negative;
    if (dxy > 0) dxy *= linear_scale_positive;
    if (dxy < 0) dxy *= linear_scale_negative;

    dx = cos(dth) * dxy;
    dy = sin(dth) * dxy;

    x_pos += 4*(cos(theta) * dx - sin(theta) * dy);
    y_pos += 4*(sin(theta) * dx + cos(theta) * dy);
    theta += dth;

    if(theta >= two_pi) theta -= two_pi;
    if(theta <= -two_pi) theta += two_pi;
    
    odom_msg.header.stamp = current_time;
    odom_msg.header.frame_id = odom;
    odom_msg.pose.pose.position.x = x_pos;
    odom_msg.pose.pose.position.y = y_pos;
    odom_msg.pose.pose.position.z = 0.0;
    odom_msg.twist.twist.linear.x = dx/(odom_msg.header.stamp.toSec() - odomOld.header.stamp.toSec());
    odom_msg.pose.pose.orientation.z = theta;
    odom_msg.twist.twist.angular.z = theta + odomOld.pose.pose.orientation.z;
    //odom_msg.pose.pose.orientation = odom_quat;
//    if (isnan(odom_msg.pose.pose.position.x) || isnan(odom_msg.pose.pose.position.y)
//     || isnan(odom_msg.pose.pose.position.z)) {
//    odom_msg.pose.pose.position.x = odomOld.pose.pose.position.x;
//    odom_msg.pose.pose.position.y = odomOld.pose.pose.position.y;
//    odom_msg.pose.pose.orientation.z = odomOld.pose.pose.orientation.z;
//  }
    if (speed_act_left == 0 && speed_act_right == 0){
      odom_msg.pose.covariance[0] = 1e-9;
      odom_msg.pose.covariance[7] = 1e-3;
      odom_msg.pose.covariance[8] = 1e-9;
      odom_msg.pose.covariance[14] = 1e6;
      odom_msg.pose.covariance[21] = 1e6;
      odom_msg.pose.covariance[28] = 1e6;
      odom_msg.pose.covariance[35] = 1e-9;
      odom_msg.twist.covariance[0] = 1e-9;
      odom_msg.twist.covariance[7] = 1e-3;
      odom_msg.twist.covariance[8] = 1e-9;
      odom_msg.twist.covariance[14] = 1e6;
      odom_msg.twist.covariance[21] = 1e6;
      odom_msg.twist.covariance[28] = 1e6;
      odom_msg.twist.covariance[35] = 1e-9;
    }
    else{
      odom_msg.pose.covariance[0] = 1e-3;
      odom_msg.pose.covariance[7] = 1e-3;
      odom_msg.pose.covariance[8] = 0.0;
      odom_msg.pose.covariance[14] = 1e6;
      odom_msg.pose.covariance[21] = 1e6;
      odom_msg.pose.covariance[28] = 1e6;
      odom_msg.pose.covariance[35] = 1e3;
      odom_msg.twist.covariance[0] = 1e-3;
      odom_msg.twist.covariance[7] = 1e-3;
      odom_msg.twist.covariance[8] = 0.0;
      odom_msg.twist.covariance[14] = 1e6;
      odom_msg.twist.covariance[21] = 1e6;
      odom_msg.twist.covariance[28] = 1e6;
      odom_msg.twist.covariance[35] = 1e3;
    }
    vx = (dt == 0)?  0 : (speed_act_left+speed_act_right)/2;
    vth = (dt == 0)? 0 : (speed_act_right-speed_act_left)/wheelbase;
    odom_msg.child_frame_id = base_link;
    odom_msg.twist.twist.linear.x = vx;
    odom_msg.twist.twist.linear.y = 0.0;
    odom_msg.twist.twist.angular.z = dth;
    
    
    geometry_msgs::Quaternion odom_quat = tf::createQuaternionMsgFromYaw(theta);
    geometry_msgs::Quaternion empty_quat = tf::createQuaternionMsgFromYaw(0);
    odomOld.pose.pose.position.x = odom_msg.pose.pose.position.x;
    odomOld.pose.pose.position.y = odom_msg.pose.pose.position.y;
    odomOld.pose.pose.orientation.z = odom_msg.pose.pose.orientation.z;
    odom_data_pub.publish(odom_msg);
}
void handle_speed( const geometry_msgs::Vector3Stamped& speed) {
  //speed_act_left = trunc(speed.vector.x*100)/100;
  speed_act_left = speed.vector.x;
  ROS_INFO("speed left : %f", speed_act_left);
  //speed_act_right = trunc(speed.vector.y*100)/100;
  speed_act_right = speed.vector.y;
  ROS_INFO("speed right : %f", speed_act_right);
  speed_dt = speed.vector.z;
  speed_time = speed.header.stamp;
}


int main(int argc, char **argv)
{
  // Launch ROS and create a node
  ros::init(argc, argv, "ekf_odom_pub");
  ros::NodeHandle node;
    // Set the data fields of the odometry message
  odom_msg.header.frame_id = "odom";
  odom_msg.pose.pose.position.z = 0;
  odom_msg.pose.pose.orientation.x = 0;
  odom_msg.pose.pose.orientation.y = 0;
  odom_msg.twist.twist.linear.x = 0;
  odom_msg.twist.twist.linear.y = 0;
  odom_msg.twist.twist.linear.z = 0;
  odom_msg.twist.twist.angular.x = 0;
  odom_msg.twist.twist.angular.y = 0;
  odom_msg.twist.twist.angular.z = 0;
  tf::TransformBroadcaster broadcaster;

  


  // Subscribe to ROS topics
  ros::NodeHandle n;
  ros::NodeHandle nh_private_("~");
  ros::Subscriber sub = n.subscribe("speed", 50, handle_speed);
  ros::Subscriber subInitialPose = node.subscribe("initial_2d", 1, set_initial_2d);
  // Publisher of simple odom message where orientation.z is an euler angle
  odom_data_pub = node.advertise<nav_msgs::Odometry>("odom_data_euler", 100);
 
  // Publisher of full odom message where orientation is quaternion
  odom_data_pub_quat = node.advertise<nav_msgs::Odometry>("odom_data_quat", 100);
  ros::Rate loop_rate(30);
  geometry_msgs::Quaternion odom_quat = tf::createQuaternionMsgFromYaw(theta);
  while(ros::ok()) {
     
    if(initialPoseRecieved) {
      update_odom();
      publish_quat();
    }
    ros::spinOnce();
    loop_rate.sleep();
  }
}
