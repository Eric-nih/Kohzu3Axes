# main program for controlling stages

# TODO: add function to move to a position
#       add function to move a relative distance
#       add funtion to home all the stages
#       start with a text interface to test the functions
#       develop a GUI interface
#       Find a way to start this by clicking on an icon in Windows

import serial
import time, asyncio
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
print("Opening Connection")
ser = serial.Serial('com4', 38400,8,"N",1,timeout=1)

# NOTE: doing one command right after another causes problems.
# We need to check if stages are idle before proceding.  EEB 5/22/2026
async def wait4idle(ser, axes):
   while True:
    allIdle = True
    for axis in axes:
        # print(idleCheck(ser, axis))
        # print("axis = ", axis)
        allIdle = allIdle and idleCheck(ser, axis)

    print("allIdle = ", allIdle)
    if allIdle:
        break

    time.sleep(1)

async def readyCheck(ser, axes):
    try:
        ready = await asyncio.wait_for(wait4idle(ser, axes), timeout=2)
        # print("ready = ", ready)
    except asyncio.TimeoutError:
        print("Error: It took to long for the controller to respond")


# home the stages
print("homing all stages")
homeAll(ser,axes)

asyncio.run(readyCheck(ser, axes))

# print("moving to (5.0,5.0, 10.3)mm" )
pulses = conv2Pulse((-3.,3.0,-50.0),dist2pulse)
print("pulses = ", pulses)
gotoPosition(ser,pulses)

ser.close()
print("End of program")