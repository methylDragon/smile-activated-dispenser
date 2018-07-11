# -*- coding: utf-8 -*-
"""
@author: methylDragon

Use this script to test the serial transmission to the connected Arduino!
"""

from time import sleep
import serial
ser = serial.Serial('COM15', 9600) # Establish the connection on a specific port
counter = 32 # Below 32 everything in ASCII is gibberish
while True:
     counter +=1
     ser.write(bytes(chr(36), 'ascii')) # Convert the decimal number to ASCII then send it to the Arduino
     print("sup")
     #print(counter, ":", ser.readline()) # Read the newest output from the Arduino
     sleep(10) # Delay for one tenth of a second
     if counter == 255:
         counter = 32
