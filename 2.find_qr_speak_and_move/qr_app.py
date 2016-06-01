#!/usr/bin/env python

import time, threading
from os.path import expanduser

# Import the RAPP Robot API
from rapp_robot_api import RappRobot
# Import the RAPP Platform API
from RappCloud import RappPlatformAPI

# Create an object in order to call the desired functions
rh = RappRobot()
ch = RappPlatformAPI()

# Enable the NAO motors for the head to move
rh.motion.enableMotors()

def callback():
    print "Callback called!"
    # Capture an image from the NAO cameras
    rh.vision.capturePhoto("/home/nao/qr.jpg", "front", "640x480")
    # Get the photo to the PC
    rh.utilities.moveFileToPC("/home/nao/qr.jpg", expanduser("~") + "/Pictures/qr.jpg")
    # Check if QRs exist
    imageFilepath = expanduser("~") + "/Pictures/qr.jpg"
    res = ch.qrDetection(imageFilepath)
    print "Call to platform finished"

    if len(res['qr_centers']) == 0: # No QR codes were detected
        print "No QR codes were detected"
    else: # One or more QR codes detected
        print "QR code detected"
        qr_center = res['qr_centers'][0]
        qr_message = res['qr_messages'][0]

        # Directions are computed bounded in [-1,1]
        dir_x = (qr_center['x'] - (640.0/2.0)) / (640.0 / 2.0)
        dir_y = (qr_center['y'] - (480.0/2.0)) / (480.0 / 2.0)
        angle_x = -dir_x * 30.0 / 180.0 * 3.1415
        angle_y = dir_y * 23.7 / 180.0 * 3.1415

        # Get NAO head angles
        ans = rh.humanoid_motion.getJointAngles(["HeadYaw", "HeadPitch"]) 
        angles = ans['angles']
        
        # Set NAO angles according to the QR center
        rh.humanoid_motion.setJointAngles(["HeadYaw", "HeadPitch"], \
                [angle_x + angles[0], angle_y + angles[1]], 0.1)

        if callback.qr_found == False:
            rh.audio.speak("I found a QR with message: " + qr_message)
            rh.audio.speak("I will track it")
            callback.qr_found = True

        # Capture an image from the NAO cameras
        rh.vision.capturePhoto("/home/nao/qr.jpg", "front", "640x480")
        # Get the photo to the PC
        rh.utilities.moveFileToPC("/home/nao/qr.jpg", expanduser("~") + "/Pictures/qr.jpg")
    
    threading.Timer(0, callback).start()


callback.qr_found = False
callback()
