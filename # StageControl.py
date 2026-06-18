# Python GUI for controlling stages

import sys, serial
import time, asyncio
import stageCommands as stageC
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QCheckBox, QToolBar) 
from PySide6.QtGui import QIcon, QKeySequence, QAction
from PySide6.QtCore import Qt

# Axes in use
axes = (1,2,3)

# conversion from mm to pulses for each axis
# These values depend on the stages
# being used and on the number of microsteps that they are
# set for
dist2pulse = (4000,4000,500) # vertical stage value appears to be 500 from measurements.

def conv2Pulse(Dist,D2P):
    """Kohzu stages move a set number of pulses. This function converts a distance in mm to the number of pulses for each axis."""
    result = list()
    for i in range(len(Dist)):
        result.append(int(Dist[i]* D2P[i]))

    return result

class MainWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Magnetic Field Measurement")

        # Initialize controller
        self.ser = serial.Serial('com4', 38400,8,"N",1,timeout=1)
        print("Opening Connection to controller")
        self.statusBar().showMessage("Connected to controller")

        # Menu
        self.menu = self.menuBar()
        file_menu = self.menu.addMenu("File")

        # Toolbar
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)

        self.label = QLabel("Let's get started!")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 24px;")
        self.setCentralWidget(self.label)

        home_action = QAction("Home all", self)
        home_action.setStatusTip("Homing all stages")
        home_action.triggered.connect(self.homeAll)
        self.toolbar.addAction(home_action)

        goStart_action = QAction("Go to start", self)
        goStart_action.setStatusTip("Going to starting position for scanning")
        goStart_action.triggered.connect(self.goStart)
        self.toolbar.addAction(goStart_action)

        self.setStatusBar(self.statusBar())

        # Exit QAction
        file_menu.addAction(QIcon.fromTheme(QIcon.ThemeIcon.ApplicationExit),
                            "Exit", QKeySequence.StandardKey.Quit, self.close)
        
        
    def homeAll(self):
        """Send all stages to home position"""
        stageC.homeAll(self.ser,axes)
        asyncio.run(stageC.readyCheck(self.ser, axes))
        self.updatePosition()

    def goStart(self):
        """Move to starting position for scanning"""
        startPos = (0.,0.,50.)
        pulsePos = conv2Pulse(startPos,dist2pulse)
        stageC.gotoPosition(self.ser, pulsePos)
        asyncio.run(stageC.readyCheck(self.ser, axes))
        self.updatePosition()

    def calculatePosition(self):
        """Calculate the current position of the stages in mm, returning a list"""
        Positions = [0.,0.,0.]
        for a in axes:
            Positions[a-1] = stageC.readPos(self.ser,a)/dist2pulse[a-1]
            # print("Position of axis ", a, " = ", Positions[a-1], " mm")
        return Positions
    
    def updatePosition(self):
        """Update the label with the current position of the stages"""
        self.label.setText("current position: " + str(self.calculatePosition()))
        self.label.update()

        
        



        
if __name__ == "__main__":
    app = QApplication([])

    widget = MainWidget()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())