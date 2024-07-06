#!/usr/bin/env python

import rospy
import actionlib
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal

def main():
    rospy.init_node('simple_navigation_goals')

    # Create the SimpleActionClient, passing the type of the action to the constructor.
    client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
    
    # Wait for the action server to come up.
    rospy.loginfo("Waiting for the move_base action server to come up")
    client.wait_for_server()

    destinations = {
        1: {"name": "diem 1", "x": -3.937, "y": -0.298, "w": 1.0},
        2: {"name": "diem 2", "x": 0.4289, "y": 0.26589, "w": 1.0},
        3: {"name": "Front Door", "x": 10.5, "y": 2.0, "w": 1.0},
        4: {"name": "Living Room", "x": 5.3, "y": 2.7, "w": 1.0},
        5: {"name": "Home Office", "x": 2.5, "y": 2.0, "w": 1.0},
        6: {"name": "Kitchen", "x": 3.0, "y": 6.0, "w": 1.0}
    }

    run = True
    while run:
        rospy.loginfo("\nWhere do you want the robot to go?")
        for key, value in destinations.items():
            rospy.loginfo(f"{key} = {value['name']}")
        user_choice = input("Enter a number: ")

        if user_choice.isdigit():
            user_choice = int(user_choice)
            if user_choice in destinations:
                selected_place = destinations[user_choice]
                goal = MoveBaseGoal()
                goal.target_pose.header.frame_id = "map"
                goal.target_pose.header.stamp = rospy.get_rostime()
                goal.target_pose.pose.position.x = selected_place['x']
                goal.target_pose.pose.position.y = selected_place['y']
                goal.target_pose.pose.orientation.w = selected_place['w']

                client.send_goal(goal)
                rospy.loginfo("Sending goal")
                client.wait_for_result()
                
                if client.get_state() == actionlib.GoalState.SUCCEEDED:
                    rospy.loginfo("The robot has arrived at the goal location")
                else:
                    rospy.loginfo("The robot failed to reach the goal location for some reason")
                
                choice_to_continue = input("Would you like to go to another destination? (Y/N) ").lower()
                if choice_to_continue == 'n':
                    run = False
            else:
#### Main Place to Note: Correcting the Orientation Setting
                rospy.loginfo("Invalid selection. Please try again.")
        else:
            rospy.loginfo("Invalid input. Please enter a number.")

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass

