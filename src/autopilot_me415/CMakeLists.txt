cmake_minimum_required(VERSION 2.8.3)
project(autopilot_me415)

find_package(catkin REQUIRED COMPONENTS
  roscpp
  rospy
  rosflight_msgs
  rosplane_msgs
  sensor_msgs
)
