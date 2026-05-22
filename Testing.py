# main program for controlling stages

# TODO: add function to move to a position
#       add function to move a relative distance
#       add funtion to home all the stages
#       start with a text interface to test the functions
#       develop a GUI interface
#       Find a way to start this by clicking on an icon in Windows

import serial
from stageCommands import *

# Axes in use
axes = (1,2,3)

# conversion from mm to pulses for each axis
# These values depend on the stages
# being used and on the number of microsteps that they are
# set for
dist2pulse = (4000,4000,500) # vertical stage value appears to be 500 from measurements.

def conv2Pulse(Dist,D2P):
    result = list()
    for i in range(len(Dist)):
        result.append(int(Dist[i]* D2P[i]))

    return result
# Initiate controller
# 
print("Opening Connection")
ser = serial.Serial('com4', 38400,8,"N",1,timeout=1)

# NOTE: doing one command right after another causes problems.
# We need to check if stages are idle before proceding.  EEB 5/22/2026

# home the stages
#print("homing all stages")
#homeAll(ser,axes)

for axis in axes:
    idleCheck(ser, axis)

#print("moving to (5.0,5.0, 10.3)mm" )
#pulses = conv2Pulse((-3.,0.0,-50.0),dist2pulse)
#print("pulses = ", pulses)
#gotoPosition(ser,pulses)

ser.close()
print("End of program")