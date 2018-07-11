# -*- coding: utf-8 -*-
"""
Smile Activated Dispenser
@author: methylDragon

                                   .     .
                                .  |\-^-/|  .
                               /| } O.=.O { |\
                              /´ \ \_ ~ _/ / `\
                            /´ |  \-/ ~ \-/  | `\
                            |   |  /\\ //\  |   |
                             \|\|\/-""-""-\/|/|/
                                     ______/ /
                                     '------'
                       _   _        _  ___
             _ __  ___| |_| |_ _  _| ||   \ _ _ __ _ __ _ ___ _ _
            | '  \/ -_)  _| ' \ || | || |) | '_/ _` / _` / _ \ ' \
            |_|_|_\___|\__|_||_\_, |_||___/|_| \__,_\__, \___/_||_|
                               |__/                 |___/
            -------------------------------------------------------
                           github.com/methylDragon

Haar Cascades Used:
https://github.com/opencv/opencv/tree/master/data/haarcascades (Face)
https://github.com/hromi/SMILEsmileD/tree/master/smileD (Smile)

Description:
This is the Python script component of the Smile Activated Dispenser, that
detects smiles that occur within detected faces using OpenCV!

If a smile is detected, a decaying counter is incremented. When the counter is
filled up, a celebratory sound is played and an optional serial command is sent
to a connected Arduino board to actuate whatever dispenser you might have!
"""

import cv2
import numpy as np
import sys
import pygame
import time
import serial

# =============================================================================
# USER-SET PARAMETERS
# =============================================================================

DEBUG = False # Print debug info

SOUND_ON = True # Play a sound when dispenser is triggered
SERIAL_ON = False # True if you have a connected Arduino

# Vary this number to make the activation less or more difficult
# Note: Too high and the dispenser becomes impossible to trigger
DIFFICULTY_FACTOR = 1 # 1 - 100 is a safe range

FRAME_H = 480 # Frame height
FRAME_W = 640 # Frame width

RESIZE = False # Resize frame
SCALING_FACTOR = 1 # Amount to resize by

USE_LOGO = True # Use a logo?
LOGO_PATH = "logo.png" # Location of logo

# Set your serial ports
if sys.platform[0:3] == "win":
    SERIAL_PORT = "COM15"
else:
    SERIAL_PORT = "/dev/ttyACM0"

# =============================================================================
# INIT
# =============================================================================

# If serial mode is on, connect with the Arduino on the specified COM port
try:
    if SERIAL_ON: ser = serial.Serial(SERIAL_PORT, 9600)
except:
    SERIAL_ON = False
    print("Serial error on", SERIAL_PORT + "! Turning serial off!")

# Give the Arduino some time to set up
time.sleep(2)

# Prep pygame sound player
pygame.mixer.pre_init(44100, 16, 2, 4096)
pygame.init()
pygame.mixer.music.load("mlg-airhorn.mp3")

# Initialise video stream
cap = cv2.VideoCapture(5) # Flush the stream
cap.release()
cap = cv2.VideoCapture(0) # Then start the webcam

# With this resolution
cap.set(3,FRAME_W) # Width
cap.set(4,FRAME_H) # Height
cap.set(21, 1) # Buffer Size

# Load Haar Cascades for smiles and faces
# And set text font
smile_cascade = cv2.CascadeClassifier('smiled_01.xml')
face_cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
font = cv2.FONT_HERSHEY_SIMPLEX

if USE_LOGO:
    try:
        logo = cv2.imread(LOGO_PATH, cv2.IMREAD_UNCHANGED)
    except:
        print("NO LOGO FOUND")
        USE_LOGO = False

# =============================================================================
# ADD EMPTY BORDERS TO LOGO
# =============================================================================

if USE_LOGO:
    logo_height, logo_width = logo.shape[:2]

    if logo_height >= logo_width:
        logo_scaling_factor = FRAME_H / logo_height / 3.5
    else:
        logo_scaling_factor = FRAME_W / logo_width / 3.5
    
    logo = cv2.resize(logo, None, fx = logo_scaling_factor, fy = logo_scaling_factor)
    
    logo_h, logo_w = logo.shape[:2]
    
    # Position of logo's bottom right corner
    logo_pos_y, logo_pos_x = FRAME_H - 10, FRAME_W - 10
    
    logo = cv2.copyMakeBorder(logo, logo_pos_y - logo_h, FRAME_H - logo_pos_y,
                              logo_pos_x - logo_w, FRAME_W - logo_pos_x,
                              cv2.BORDER_CONSTANT)

# =============================================================================
# USEFUL FUNCTIONS
# =============================================================================

# Source: https://stackoverflow.com/questions/40895785/using-opencv-to-overlay-transparent-image-onto-another-image
def blend_transparent(background, overlay):

    # Split out the transparency mask from the colour info
    size = overlay.shape[2]
    
    overlay_img = overlay[:,:,:3] # Grab the BGR planes
    
    if size == 4:
        overlay_mask = overlay[:,:,3:]  # And the alpha plane
    else:
        overlay_mask = overlay[:,:,2:]

    # Again calculate the inverse mask
    background_mask = 255 - overlay_mask

    # Turn the masks into three channel, so we can use them as weights
    overlay_mask = cv2.cvtColor(overlay_mask, cv2.COLOR_GRAY2BGR)
    background_mask = cv2.cvtColor(background_mask, cv2.COLOR_GRAY2BGR)

    # Create a masked out face image, and masked out overlay
    # We convert the images to floating point in range 0.0 - 1.0
    background_output = (background * (1 / 255.0)) * (background_mask * (1 / 255.0))
    overlay_output = (overlay_img * (1 / 255.0)) * (overlay_mask * (1 / 255.0))

    # And finally just add them together, and rescale it back to an 8bit integer image
    return np.uint8(cv2.addWeighted(background_output, 255.0, overlay_output, 255.0, 0.0))

# =============================================================================
# CORE CODE
# =============================================================================

# Initialise variables
counter = 0
text = "Smile! " + str(int(counter)) # This text value is overlayed!

# Begin core loop
while True:

    # Create a window showing the video stream
    ret, frame = cap.read()

    # Create a version of it in greyscale in memory
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Find positions of all detected faces!
    faces = face_cascade.detectMultiScale(gray, 1.3, 3)

    # Set the flag for incrementing the counter
    add_flag = False

    # Iterate through the faces
    for (x,y,w,h) in faces:

        # And draw a marking rectangle for face
        cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)

        # But also save the bottom half of each face
        # As a region of interest (roi)
        
        offset = int(2*h/3)
        
        roi_gray = gray[y+offset:y+h+5, x:x+w]
        roi_colour = frame[y+offset:y+h+5, x:x+w]

        # Detect smiles within each region of interest (each face bottom-half!)
        # This helps to reduce false-positives!

        smiles = smile_cascade.detectMultiScale(roi_gray, 1.3, 3)

        # Iterate through detected smiles
        for (sx, sy, sw, sh) in smiles:
            # And draw a marking rectangle
            cv2.rectangle(frame, (sx+x, sy+y+offset), (sx+sw+x, sy+sh+y+offset), (0,255,0), 1)

            add_flag = True

            # Uncomment to show the smile
            #cv2.imshow("Smile", frame[sy+y+offset:sy+sh+y+offset, sx+x:sx+sw+x])

    if counter > -100 and add_flag: counter += 12

    # After all detection is done, update the text shown on the screen
    cv2.putText(frame, str(text), (30,50), font, 1, (255,255,255), 3, cv2.LINE_AA)

    # Change the text depending on the counter
    if counter > -180 and counter < -140:
        text = "Take your reward!"

    if counter > -140 and counter < -101:
        text = "O.=.O"

    if counter > -100 :

        # If the counter is positive, decay the counter if no smiles detected
        if counter > 0:
            counter -= (1 + (counter ** 1.500) / 108.5) + 0.00075 * DIFFICULTY_FACTOR
            text = "Smile! " + str(int(counter)) # Also print the counter
            cv2.line(frame, (640,480),(640,470-int(counter*4.7)),(0,255,0),20)
        else:
            text = "Smile! c:" # Otherwise, just prompt for smiles
            counter -= 0.5
    else:
        counter += 1.5 # Have the counter slowly increment if it's too low
        if counter < -101:
            cv2.line(frame, (640,int((counter + 200) * 4.8)),(640,480),(0,165,255),20)

    # Trigger when counter reaches 100
    if counter > 100:
        text = "DISPENSE! .(^u^.)" # Change the text!
        try:
            if SERIAL_ON: ser.write(bytes("$", 'ascii')) # Send byte to Arduino
        except:
            print("MESSAGE DROPPED")
            text = "MESSAGE DROPPED" # Change the text!
        counter = -200 # Set counter to low number for delay
        if SOUND_ON:
            pygame.mixer.music.play() # Play a sound!
            pygame.mixer.music.play() # Play a sound!

    if DEBUG: print(counter)

    if USE_LOGO:
        frame = blend_transparent(frame, logo)

    if RESIZE: frame = cv2.resize(frame, None, fy = SCALING_FACTOR, fx = SCALING_FACTOR)

    # Update the window showing the video stream with the next frame
    cv2.imshow("Frame", frame)

    # Interrupt trigger by pressing q to quit the open CV program
    ch = cv2.waitKey(1)
    if ch & 0xFF == ord('q'):
        break


# Cleanup when closed
cv2.waitKey(0)
cv2.destroyAllWindows()
cap.release()
if SERIAL_ON: ser.close()
