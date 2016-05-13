#!/usr/bin/env python

# Author: Chrisa Gouniotou (https://github.com/chrisagou)

# Import the RAPP Robot API
from rapp_robot_api import RappRobot

rh = RappRobot()


rh.humanoid_motion.goToPosture("Sit", 0.7)
rh.motion.disableMotors()


