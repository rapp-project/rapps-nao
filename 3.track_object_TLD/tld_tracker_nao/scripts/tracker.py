#!/usr/bin/env python

# Authors: 
#   Chrisa Gouniotou (https://github.com/chrisagou)
#   Aspa Karanasiou (https://github.com/aspa1)

# Import the RAPP Robot API
from rapp_robot_api import RappRobot

from geometry_msgs.msg import Polygon
from geometry_msgs.msg import Twist

from naoqi_bridge_msgs.msg import JointAnglesWithSpeed

import rospy
import sys
import time

class NaoTldTracker:

    def __init__(self):
        self.rh = RappRobot()

        # Use naoqi_brdge to move the head
        self.joint_pub = rospy.Publisher('/joint_angles', JointAnglesWithSpeed, queue_size=1)

        # NAO stands up
        self.rh.motion.enableMotors()
        self.rh.humanoid_motion.goToPosture("Stand", 0.7)

        self.lost_object_counter = 20
        self.lock_motion = False
        self.hunt_initiated = False

        # These are the NAO body velocities. They are automatically published
        # in the self.set_velocities_callback
        self.x_vel = 0
        self.y_vel = 0
        self.theta_vel = 0

        # Subscription to the TLD tracking alerts
        self.predator_sub = rospy.Subscriber("/vision/predator_alert", \
                Polygon, self.track_bounding_box)

        # Timer callback to check if tracking has been lost
        rospy.Timer(rospy.Duration(0.1), self.lost_object_callback)
        # Callback to set the velocities periodically
        rospy.Timer(rospy.Duration(0.1), self.set_velocities_callback)

    # Callback of the TLD tracker. Called when the object has been detected
    def track_bounding_box(self, polygon):
        self.hunt_initiated = True

        # Set the timeout counter to 2 seconds
        self.lost_object_counter = 20
        
        # Velocities message initialization
        joint = JointAnglesWithSpeed()
        joint.joint_names.append("HeadYaw")
        joint.joint_names.append("HeadPitch")
        joint.speed = 0.1
        joint.relative = True

        # Get center of detected object and calculate the head turns
        target_x = polygon.points[0].x + 0.5 * polygon.points[1].x
        target_y = polygon.points[0].y + 0.5 * polygon.points[1].y

        sub_x = target_x - 320 / 2.0
        sub_y = target_y - 240 / 2.0

        var_x = (sub_x / 160.0)
        var_y = (sub_y / 120.0)

        joint.joint_angles.append(-var_x * 0.05)
        joint.joint_angles.append(var_y * 0.05)

        [ans, err] = self.rh.humanoid_motion.getJointAngles(['HeadYaw', 'HeadPitch'])
        head_pitch = ans[1]
        head_yaw = ans[0]

        # Get the sonar measurements
        sonars = self.rh.sensors.getSonarsMeasurements()[0]

        # Check if NAO is close to an obstacle
        if sonars['front_left'] <= 0.3 or sonars['front_right'] <= 0.3:
            self.lock_motion = True
            rospy.loginfo("Locked due to sonars")
        # Check if NAOs head looks way too down or up
        elif head_pitch >= 0.4 or head_pitch <= -0.4:
            self.lock_motion = True
            rospy.loginfo("Locked due to head pitch")
        # Else approach the object
        elif self.lock_motion is False:
            self.theta_vel = head_yaw * 0.1
            if -0.2 < head_yaw < 0.2:
                print "Approaching"
                self.x_vel = 0.5
                self.y_vel = 0.0
            else:
                self.x_vel = 0.0
                self.y_vel = 0.0
                print "Centering"
            self.joint_pub.publish(joint)

        # Check the battery levels
        [batt, none] = self.rh.sensors.getBatteryLevels()
        battery = batt[0]
        if battery < 25:
            self.rh.audio.setVolume(100)
            self.rh.audio.speak("My battery is low")
            self.predator_sub.unregister()
            self.rh.humanoid_motion.goToPosture("Sit", 0.7)
            self.rh.motion.disableMotors()
            sys.exit(1)

    # Callback invoked every 0.1 seconds to check for lost of object tracking
    def lost_object_callback(self, event):
        # Continues only after the user has selected an object
        if self.hunt_initiated:
            self.lost_object_counter -= 1
            # If 2 seconds have passed without tracking activity the robot stops
            if self.lost_object_counter < 0:
                self.lock_motion = True
                self.x_vel = 0.0
                self.y_vel = 0.0
                self.theta_vel = 0.0
                rospy.loginfo("Locked due to 2 seconds of non-tracking")

                self.predator_sub.unregister()

    # Callback to periodically (0.1 sec) set velocities, except from the 
    # case where the robot has locked its motion
    def set_velocities_callback(self, event):
        if not self.lock_motion:
            self.rh.motion.moveByVelocity(self.x_vel, self.y_vel, \
                    self.theta_vel)
        else:
            self.rh.motion.moveByVelocity(0, 0, 0)

# The main function
if __name__ == "__main__":
    rospy.init_node('nao_tld_tracker', anonymous = True)
    nao = NaoTldTracker()
    rospy.spin()
