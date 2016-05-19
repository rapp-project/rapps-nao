#!/usr/bin/env python

import time, threading, math
# Import the RAPP Robot API
from rapp_robot_api import RappRobot
# Import the vision modules
from RappCloud.CloudMsgs import QrDetection
from RappCloud.CloudMsgs import FaceDetection
from RappCloud.CloudMsgs import ObjectRecognitionCaffe
from RappCloud.CloudMsgs import OntologySuperclasses

from RappCloud import RappPlatformService

# Transforms a point in an image frame to rads. x_fov and y_fov are in degrees
def pointToRads(x, y, x_pixels, y_pixels, x_fov, y_fov):
    return [
            (x - x_pixels / 2.0) / (x_pixels / 2.0) * x_fov / 2.0 / 180.0 * 3.1415, 
            (y - y_pixels / 2.0) / (y_pixels / 2.0) * y_fov / 2.0 / 180.0 * 3.1415
            ]

# Create an object in order to call the desired functions
rh = RappRobot('192.168.0.100', 9559)
# Instantiate new vision services.
qr_msg = QrDetection()
face_msg = FaceDetection()
obj_msg = ObjectRecognitionCaffe()
onto_msg = OntologySuperclasses()

svc = RappPlatformService()

# Enable the NAO motors for the head to move
rh.motion.enableMotors()

# rh.audio.speak('I will scan for objects')

objects = {}
qr_messages = []

global_counter = 0
for i in range(0, 3):
    for j in range(0, 3):

        global_counter += 1

        head_angles = [-0.3 + 0.3 * i, -0.3 + 0.3 * j]
        rh.humanoid_motion.setJointAngles(["HeadYaw", "HeadPitch"], head_angles, 0.5)

        # Delay to stabilize the head
        time.sleep(1)

        image_name = "img_" + str(i * 3 + j) + ".jpg"
        # Capture an image from the NAO cameras
        rh.vision.capturePhoto("/home/nao/" + image_name, "front", "640x480")
        # Get the photo to the PC
        rh.utilities.moveFileToPC("/home/nao/" + image_name, "/home/manos/rapp_nao/" + image_name)
        
        # Check if objects exist
        qr_msg.req.imageFilepath = "/home/manos/rapp_nao/" + image_name
        face_msg.req.imageFilepath = "/home/manos/rapp_nao/" + image_name
        obj_msg.req.imageFilepath = "/home/manos/rapp_nao/" + image_name
        
        # Get the responses
        qr_resp = svc.call(qr_msg)
        face_resp = svc.call(face_msg)
        obj_resp = svc.call(obj_msg)

        # Store the objects and the respective head angles
        if len(qr_resp.qr_centers) != 0:
            obj_frame_ang = pointToRads(
                    qr_resp.qr_centers[0]['x'],
                    qr_resp.qr_centers[0]['y'],
                    640.0,
                    480.0,
                    60.97,
                    47.64)
                    
            obj_ang = [
                    head_angles[0] - obj_frame_ang[0],
                    head_angles[1] + obj_frame_ang[1]
                    ]
            if qr_resp.qr_messages[0] not in qr_messages:
                objects["qr " + qr_resp.qr_messages[0]] = obj_ang

        elif len(face_resp.faces) != 0:
            f_x = (face_resp.faces[0]['up_left_point']['x'] + \
                    face_resp.faces[0]['down_right_point']['x']) / 2.0
            f_y = (face_resp.faces[0]['up_left_point']['y'] + \
                    face_resp.faces[0]['down_right_point']['y']) / 2.0

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
            # Check if the same face has been detected before
            to_be_inserted = True
            for k in objects:
                if "face" in k:
                    # Check angle proximity
                    if math.fabs(objects[k][0] - obj_ang[0]) > 0.1 or \
                            math.fabs(objects[k][1] - obj_ang[1]) > 0.1:
                        to_be_inserted = False
            if to_be_inserted:
                objects["face " + str(global_counter)] = obj_ang

        time.sleep(1)
 
print objects
counter = 0
for key in objects:
    counter += 1
    rh.audio.speak("I have found a " + key)
    rh.humanoid_motion.setJointAngles(
            ["HeadYaw", "HeadPitch"],
            objects[key],
            0.5
            )
    time.sleep(2)
    image_name = "results_" + str(counter) + ".jpg"
    # Capture an image from the NAO cameras
    rh.vision.capturePhoto("/home/nao/" + image_name, "front", "640x480")
    # Get the photo to the PC
    rh.utilities.moveFileToPC("/home/nao/" + image_name, "/home/manos/rapp_nao/" + image_name)


