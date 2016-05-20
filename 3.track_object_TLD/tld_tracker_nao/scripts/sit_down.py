#!/usr/bin/env python

# Import the RAPP Robot API
from rapp_robot_api import RappRobot

rh = RappRobot()


rh.humanoid_motion.goToPosture("Sit", 0.7)
rh.motion.disableMotors()


