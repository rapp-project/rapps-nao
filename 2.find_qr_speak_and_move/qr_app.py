#!/usr/bin/env python

import time, threading
# Import the RAPP Robot API
from rapp_robot_api import RappRobot
# Import the QR detection module
from RappCloud import QrDetection

# Create an object in order to call the desired functions
rh = RappRobot()
# Instantiate a new FaceDetection service.
qrDetector = QrDetection(image='')

# Enable the NAO motors for the head to move
rh.motion.enableMotors()

def callback():
    print "Callback called!"
    # Capture an image from the NAO cameras
    rh.vision.capturePhoto("/home/nao/qr.jpg", "front", "640x480")
    # Get the photo to the PC
    rh.utilities.moveFileToPC("/home/nao/qr.jpg", "/home/manos/rapp_nao/qr.jpg")
    # Check if QRs exist
    qrDetector.image = "/home/manos/rapp_nao/qr.jpg"
    res = qrDetector.call()
    print "Call to platform finished"

    if len(res.qr_centers) == 0: # No QR codes were detected
        print "No QR codes were detected"
        threading.Timer(0, callback).start()
        return
    else: # One or more QR codes detected
        print "QR code detected"
        qr_center = res.qr_centers[0]
        qr_message = res.qr_messages[0]

        # Directions are computed bounded in [-1,1]
        dir_x = (qr_center['x'] - (640.0/2.0)) / (640.0 / 2.0)
        dir_y = (qr_center['y'] - (480.0/2.0)) / (480.0 / 2.0)
        angle_x = -dir_x * 30.0 / 180.0 * 3.1415
        angle_y = dir_y * 23.7 / 180.0 * 3.1415

        # Set NAO angles according to the QR center
        rh.humanoid_motion.setJointAngles(["HeadYaw", "HeadPitch"], \
                [angle_x, angle_y], 0.1)

        rh.audio.speak(qr_message)

        # Capture an image from the NAO cameras
        rh.vision.capturePhoto("/home/nao/qr.jpg", "front", "640x480")
        # Get the photo to the PC
        rh.utilities.moveFileToPC("/home/nao/qr.jpg", "/home/manos/rapp_nao/qr.jpg")


callback()
