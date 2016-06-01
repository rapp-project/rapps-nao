#!/usr/bin/env python

import time
import threading
import math
import string
from os.path import expanduser

# Import the RAPP Robot API
from rapp_robot_api import RappRobot
# Import the RAPP Platform API
from RappCloud import RappPlatformAPI

# Transforms a point in an image frame to rads. x_fov and y_fov are in degrees
def pointToRads(x, y, x_pixels, y_pixels, x_fov, y_fov):
    return [
            (x - x_pixels / 2.0) / (x_pixels / 2.0) * x_fov / 2.0 / 180.0 * 3.1415, 
            (y - y_pixels / 2.0) / (y_pixels / 2.0) * y_fov / 2.0 / 180.0 * 3.1415
            ]

# Method for NAO to point one of its hands to a certain direction
def pointToDirection(rh, angles):

    head_yaw = angles[0]
    head_pitch = angles[1]

    # The Shoulder Roll cannot go below -18.0
    limit = 18.0 / 180.0 * 3.1415

    joints = []
    
    # We prefer the Right hand
    if head_yaw < -limit:
        joints = ["RShoulderRoll", "RShoulderPitch", "RElbowRoll"]
        head_yaw = -head_yaw
    # Else the Left is selected
    else:
        joints = ["LShoulderRoll", "LShoulderPitch", "LElbowRoll"]

    # Give the command to the hand
    rh.humanoid_motion.setJointAngles(
            joints,
            [head_yaw, head_pitch, -0.0349],
            0.2)

# Create an object in order to call the desired functions
rh = RappRobot()
ch = RappPlatformAPI()

home = expanduser("~") + '/Pictures/'

rh.audio.speak('I will scan for objects')

objects = {}
qr_messages = []

global_counter = 0

# Loop to perform search in 9 directions
for i in range(0, 3):
    for j in range(0, 3):

        global_counter += 1

        # The 9 directions are [-0.3, 0, 0.3] x [-0.3, 0, 0.3] for each
        # of the Headyaw and HeadPitch joints
        head_angles = [-0.3 + 0.3 * i, -0.3 + 0.3 * j]

        # Enable the NAO motors for the head to move
        rh.motion.enableMotors()

        rh.humanoid_motion.setJointAngles(["HeadYaw", "HeadPitch"], head_angles, 0.5)

        # Disable the motion
        rh.motion.disableMotors()

        # Delay to stabilize the head
        time.sleep(1)

        image_name = "img_" + str(i * 3 + j) + ".jpg"
        # Capture an image from the NAO cameras
        rh.vision.capturePhoto("/home/nao/" + image_name, "front", "640x480")
        # Get the photo to the PC
        rh.utilities.moveFileToPC("/home/nao/" + image_name, \
            home + image_name)
        
        imageFilepath = home + image_name
        
        # Get the responses
        qr_resp = ch.qrDetection(imageFilepath)
        face_resp = ch.faceDetection(imageFilepath, False)
        obj_resp = ch.objectRecognitionCaffe(imageFilepath)

        # Prints for debugging purposes
        print str(global_counter) + ": " + str(qr_resp)
        print str(global_counter) + ": " + str(face_resp)
        print str(global_counter) + ": " + str(obj_resp)
        print "\n"

        # Store the objects and the respective head angles
        # Store the unique QR codes
        if len(qr_resp['qr_centers']) != 0:
            # Transform Image-frame angles to NAO-frame
            obj_frame_ang = pointToRads(
                    qr_resp['qr_centers'][0]['x'],
                    qr_resp['qr_centers'][0]['y'],
                    640.0,
                    480.0,
                    60.97,
                    47.64)
                    
            obj_ang = [
                    head_angles[0] - obj_frame_ang[0],
                    head_angles[1] + obj_frame_ang[1]
                    ]

            # Store the QR if it has not been stored again
            if qr_resp['qr_messages'][0] not in qr_messages:
                objects["qr " + qr_resp['qr_messages'][0]] = obj_ang

        # Store the unique faces based on location
        if len(face_resp['faces']) != 0:
            f_x = (face_resp['faces'][0]['up_left_point']['x'] + \
                    face_resp['faces'][0]['down_right_point']['x']) / 2.0
            f_y = (face_resp['faces'][0]['up_left_point']['y'] + \
                    face_resp['faces'][0]['down_right_point']['y']) / 2.0

            # Transform the Image-angles to NAO-angles
            obj_frame_ang = pointToRads(
                    f_x,
                    f_y,
                    640.0,
                    480.0,
                    60.97,
                    47.64)
            obj_ang = [
                    head_angles[0] - obj_frame_ang[0],
                    head_angles[1] + obj_frame_ang[1]
                    ]

            # Check if the same face has been detected before based on the angles
            to_be_inserted = True
            for k in objects:
                if "face" in k:
                    # Check angle proximity
                    if math.fabs(objects[k][0] - obj_ang[0]) < 0.2 and \
                            math.fabs(objects[k][1] - obj_ang[1]) < 0.2:
                        to_be_inserted = False
            if to_be_inserted:
                objects["face " + str(global_counter)] = obj_ang

        # Insert objects detected by Caffe
        if obj_resp['object_class'] != "":

            # Check if the detected objects are really there
            detected_objects = string.split(obj_resp['object_class'], ',')
            rh.audio.speak("The objects I saw are.")

            for o in detected_objects:
                rh.audio.speak(o)
            rh.audio.speak("Does any of them exist?")

            ans = rh.audio.speechDetection(['yes', 'no'], 3, 'English')
            if ans['error'] == None and ans['word'] == 'yes':
                # If they exist store them, having as angles the head angles
                objects["caffe_" + str(detected_objects[0]) + "_" + str(global_counter)] =\
                    [head_angles[0], head_angles[1]]

        time.sleep(1)

# Report the findings
counter = 0
rh.motion.enableMotors()

for key in objects:
    counter += 1

    found = key
    # If the object is from Caffe take the useful part
    if "caffe" in key:
        spl = string.split(key, '_')
        found = spl[1]

    # Nao tells what it has found
    rh.audio.speak("I have found a " + found)

    # Nao turns its face towards there
    rh.humanoid_motion.setJointAngles(
            ["HeadYaw", "HeadPitch"],
            objects[key],
            0.5
            )
    # Nao points towards this object using its arm
    pointToDirection(rh, objects[key])
    # Wait till the motion is over
    time.sleep(4)

    # Take a picture and store it for reference
    image_name = "results_" + str(key.replace(' ', '_')) + "_" + str(counter) + ".jpg"
    # Capture an image from the NAO cameras
    rh.vision.capturePhoto("/home/nao/" + image_name, "front", "640x480")
    # Get the photo to the PC
    rh.utilities.moveFileToPC("/home/nao/" + image_name, \
            home + image_name)

# Finally, NAo returns to Sit position and shuts the motors down
rh.humanoid_motion.goToPosture("Sit", 0.5)
rh.motion.disableMotors()
