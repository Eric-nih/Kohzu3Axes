# Kohzu3Axes

## Hardware
This project uses three motorized linear stages from Kohzu, along with a SC-410
controller.  It is connected to the control computer by an RS-232 cable.
- controller: Kohzu SC-410
- Vertical stage: Kohzu ZA10A-X1T
- Horizontal xy stage: YA10A-R101
- Magnetic field meter: List-Magnetik MP-4000
- optical breadboard: ThorLabs 973/579-7227
- miscellaneous holders and clamps to hold magnet and probe for magnetic field meter

## Software
A program written in Python 3 is used to control the setup.  Dependencies include
PySide6 which is a Python version of Qt, pyserial

## TODO
- It would be helpful if the current position is updated while running scans.  This will require
multithreading, along with updating the GUI.

- Add scanning in 3D.
- add controls to change com ports for magnetic field meter and for stage controller
- add plot of field measurements vs position

## DONE
- added display of field measurments, 8/5/2026
- added data storage of time, position, field measurement, and field units, 8/6/2026
- added control to change magnetic field units, 8/7/2026
- added powershell script file and shortcut on desktop

Eric Bennett
*Research Engineer,
National Institutes of Health,
NHLBI/DIR Electronic Fabrication & Design shop
bennette@mail.nih.gov*