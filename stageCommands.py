# homeAll.py
# Use the ORG command on all axes
import prepCommand as prepC

def homeAll(ser,axesTuple):

    for axis in axesTuple:
        homeCommand = "ORG"
        homeCommand += str(axis)
        homeCommand += "/2/0/0/3/0"
        ser.write(prepC.prepCommand(homeCommand))
        print(ser.readline().decode().strip())

    return

def gotoPosition(ser,Pos):
    # Pos needs xyz coordinates
    for i in range(len(Pos)):
        command = "APS"
        command += str(i+1)
        command += "/2/0/0/"
        command += str(Pos[i]) # number of pulses
        command += "/3/0/0"
        ser.write(prepC.prepCommand(command))
        print(ser.readline().decode().strip())
    return

def moveRelative(ser,Dist):
    # Dist needs xyz distances
    for i in range(len(Dist)):
        command = "RPS"
        command += str(i+1)
        command += "/2/0/0/"
        command += str(Dist[i]) 
        command += "/3/0/0"
        ser.write(prepC.prepCommand(command))
        print(ser.readline().decode().strip())
    return

def idleCheck(ser, a):
    command = "STR1/"
    command += str(a)
    ser.write(prepC.prepCommand(command))
    print(ser.readline().decode().strip())
