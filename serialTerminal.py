# Serial Port Terminal program
# Kohzu stage controllers need special characters that are not easy to send with programs such as PuTTy
# Eventually, I will add specific commands used by the controllers.
# dependencies: pyserial
# Eric Bennett, research engineer
# National Institutes of Health, NHLBI, Electronic Fabrication & Design Lab
import serial
from prepCommand import prepCommand

print("Kohzu Terminal")
ser = serial.Serial('com4', 38400,8,"N",1,timeout=1)

command = ""
while True:

    command = input('Enter a command: ')
    if command.lower() == 'exit':
        break
    else:
        ser.write(prepCommand(command))
        print(ser.readline().decode().strip())

ser.close()
print("End of program")