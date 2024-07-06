#include <ros/ros.h>
#include <tf/transform_broadcaster.h>
#include <nav_msgs/Odometry.h>
#include <geometry_msgs/Vector3Stamped.h>
#include <tf2/LinearMath/Quaternion.h>
#include <cmath>

double radius = 0.05;                              // Wheel radius, in m
double wheelbase = 0.33;                          // Wheelbase, in m
double two_pi = 6.28319;
double speed_act_left = 0.0;
double speed_act_right = 0.0;
double speed_dt = 0.0;
double x_pos = 0.0;
double y_pos = 0.0;
double theta = 0.0;
double vx = 0.0;
double vy = 0.0;
double vth = 0.0;
ros::Time current_time;
ros::Time speed_time(0.0);

void handle_speed(const geometry_msgs::Vector3Stamped& speed) {
  speed_act_left = speed.vector.x;
  ROS_INFO("speed left : %f", speed_act_left);
  speed_act_right = speed.vector.y;
  ROS_INFO("speed right : %f", speed_act_right);
  speed_dt = speed.vector.z;
  speed_time = speed.header.stamp;
}

int main(int argc, char** argv){
  ros::init(argc, argv, "ekf_odom_pub");
  ros::NodeHandle n;
  ros::NodeHandle nh_private_("~");
  ros::Subscriber sub = n.subscribe("speed", 50, handle_speed);
  ros::Publisher odom_pub = n.advertise<nav_msgs::Odometry>("odom", 50);
  ros::Publisher odom_data_pub_quat = n.advertise<nav_msgs::Odometry>("odom_data_quat", 100);
  tf::TransformBroadcaster broadcaster;
  double rate = 10.0;
  double linear_scale_positive = 1.0;
  double linear_scale_negative = 1.0;
  double angular_scale_positive = 1.0;
  double angular_scale_negative = 1.0;
  bool publish_tf = true;

  nh_private_.getParam("publish_rate", rate);
  nh_private_.getParam("publish_tf", publish_tf);
  nh_private_.getParam("linear_scale_positive", linear_scale_positive);
  nh_private_.getParam("linear_scale_negative", linear_scale_negative);
  nh_private_.getParam("angular_scale_positive", angular_scale_positive);
  nh_private_.getParam("angular_scale_negative", angular_scale_negative);

  ros::Rate r(rate);

  while(n.ok()){
    ros::spinOnce();
    current_time = speed_time;
    double dt = speed_dt;                // Time in s
    double dxy = (speed_act_left + speed_act_right) * dt / 2;
    double dth = ((speed_act_right - speed_act_left) * dt) / wheelbase;

    if (dth > 0) dth *= angular_scale_positive;
    if (dth < 0) dth *= angular_scale_negative;
    if (dxy > 0) dxy *= linear_scale_positive;
    if (dxy < 0) dxy *= linear_scale_negative;

    theta += dth;
    if(theta >= two_pi) theta -= two_pi;
    if(theta <= -two_pi) theta += two_pi;

    double dx = dxy * cos(theta);
    double dy = dxy * sin(theta);

    x_pos += dx;
    y_pos += dy;

    geometry_msgs::Quaternion odom_quat = tf::createQuaternionMsgFromYaw(theta);

    if(publish_tf) {
      current_time = ros::Time::now(); // Update current time
      geometry_msgs::TransformStamped t;
      t.header.frame_id = "/odom";
      t.child_frame_id = "/base_link";
      t.transform.translation.x = x_pos;
      t.transform.translation.y = y_pos;
      t.transform.translation.z = 0.0;
      t.transform.rotation = odom_quat;
      t.header.stamp = current_time; // Use the updated time
      broadcaster.sendTransform(t);
    }

    nav_msgs::Odometry odom_msg;
    odom_msg.header.stamp = current_time;
    odom_msg.header.frame_id = "/odom";
    odom_msg.child_frame_id = "/base_link";
    odom_msg.pose.pose.position.x = x_pos;
    odom_msg.pose.pose.position.y = y_pos;
    odom_msg.pose.pose.position.z = 0.0;
    odom_msg.pose.pose.orientation = odom_quat;
    odom_msg.twist.twist.linear.x = dxy / dt;
    odom_msg.twist.twist.linear.y = 0.0;
    odom_msg.twist.twist.linear.z = 0.0;
    odom_msg.twist.twist.angular.x = 0.0;
    odom_msg.twist.twist.angular.y = 0.0;
    odom_msg.twist.twist.angular.z = dth / dt;

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

    odom_pub.publish(odom_msg);
    ROS_INFO("quang duong : %f", odom_msg.pose.pose.position.x);

    // Publish Quaternion Odometry
    tf2::Quaternion q;
    q.setRPY(0, 0, theta); // Ensure the correct angle for the quaternion

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

    for(int i = 0; i < 36; i++) {
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

    r.sleep();
  }
}

