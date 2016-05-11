#!/usr/bin/env python

# Import the RAPP Robot API
from rapp_robot_api import RappRobot
# Create an object in order to call the desired functions
rh = RappRobot()

# Adjust the NAO master volume and ask for instructions. The valid commands are 'stand' and 'sit' and NAO waits for 5 seconds
rh.audio.setVolume(50)
rh.audio.speak("Hello there! What do you want me to do? I can sit or stand.")
[r, e] = rh.audio.speechDetection(['sit', 'stand'], 5)

# Check which command was dictated by the human
if r[0] == 'sit':
    # The motors must be enabled for NAO to move
    rh.motion.enableMotors()
    # NAO sits with 75% of its maximum speed
    rh.humanoid_motion.goToPosture('Sit', 0.75)
elif r[0] == 'stand':
    # The motors must be enabled for NAO to move
    rh.motion.enableMotors()
    # NAO stands with 75% of its maximum speed
    rh.humanoid_motion.goToPosture('Stand', 0.75)
else:
    # No command was dictated or the command was not understood
    pass

# Ask the human what movement to do: move the hands or the head?
rh.audio.speak("Do you want me to move my hands or my head?")
[r, e] = rh.audio.speechDetection(['hands', 'head'], 5)

rh.motion.enableMotors()
if r[0] == 'hands':
    rh.audio.speak("Do you want me to open the left or right hand?")
    [res, err] = rh.audio.speechDetection(['left', 'right'], 5)
    if res[0] == 'left':
        rh.humanoid_motion.openHand('Left')
    elif res[0] == 'right':
        rh.humanoid_motion.openHand('Right')
    else:
        pass

    rh.audio.speak("I will close my hands now")
    rh.humanoid_motion.closeHand('Right')
    rh.humanoid_motion.closeHand('Left')
elif r[0] == 'head':
    rh.audio.speak("Do you want me to turn my head left or right?")
    [res, err] = rh.audio.speechDetection(['left', 'right'], 5)

    # The head moves by 0.4 rads left or right with 50% of its maximum speed
    if res[0] == 'left':
        rh.humanoid_motion.setJointAngles(['HeadYaw'], [-0.4], 0.5)
    elif res[0] == 'right':
        rh.humanoid_motion.setJointAngles(['HeadYaw'], [0.4], 0.5)
    else:
        pass

    rh.audio.speak("I will look straight now")
    rh.humanoid_motion.setJointAngles(['HeadYaw'], [0], 0.5)
else:
    pass

rh.audio.speak("And now I will sit down and sleep!")
rh.humanoid_motion.goToPosture('Sit', 0.7)
rh.motion.disableMotors()
