# Python GUI for controlling stages

import sys, serial
import time, asyncio
import stageCommands as stageC
#from MPprepCommand import prepCommand as mpPrep
import meterCommands as meterC
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QCheckBox, QPushButton, QToolBar, QHBoxLayout,
    QFormLayout,QVBoxLayout, QWidget, QPushButton, QDoubleSpinBox, QSpinBox, 
    QTabWidget, QFrame
)
from PySide6.QtGui import QIcon, QKeySequence, QAction, QFont
from PySide6.QtCore import Qt, QTimer

# Axes in use
axes = (1,2,3)

# conversion from mm to pulses for each axis
# These values depend on the stages being used 
# and on the number of microsteps that they are set for
 
dist2pulse = (4000,4000,500) # vertical stage value appears to be 500 from measurements.

def conv2Pulse(Dist,D2P) -> float | None:
    """Kohzu stages move a set number of pulses. This function converts a distance in mm 
    to the number of pulses for each axis."""
    if(isinstance(Dist,(list,tuple))):
        result = list()
        for i in range(len(Dist)):
            result.append(int(Dist[i]* D2P[i]))
        return result
    elif(isinstance(Dist,(float,int))):
        return(Dist * D2P)
    else:
        print("ERROR: unkown data Type")
        return None
              

class MainWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Magnetic Field Measurement")

        # Initialize controller
        self.ser = serial.Serial('com6', 38400,8,"N",1,timeout=1)
        print("Opening Connection to controller")
        self.statusBar().showMessage("Connected to controller")

        self.mpSer = serial.Serial('Com5',115200,8,"N",1,timeout=1)
        print("Opening connection to meter")

        widget = QWidget()
        self.setCentralWidget(widget)

        # Menu
        self.menu = self.menuBar()
        file_menu = self.menu.addMenu("File")

        # Toolbar
        self.toolbar = QToolBar("Main Toolbar")
        
        self.addToolBar(self.toolbar)

        mainLayout = QHBoxLayout()
        
        graphLayout = QVBoxLayout()
        tabs = QTabWidget(self)

        gotoPage = QWidget(self)
        gotoLayout = QFormLayout()
        scanLayout = QFormLayout()
        gotoPage.setLayout(gotoLayout)
        scanPage = QWidget(self)
        scanPage.setLayout(scanLayout)
        meterPage = QWidget(self)
        meterLayout = QFormLayout()
        meterPage.setLayout(meterLayout)

        mainLayout.addWidget(tabs)

        # set up the form to go to a position
        self.gotoButton = QPushButton("Go to position")
        self.gotoX = QDoubleSpinBox()
        self.gotoY = QDoubleSpinBox()
        self.gotoZ = QDoubleSpinBox()
        gotoLayout.addRow(self.gotoButton)
        gotoLayout.addRow("X (mm)",self.gotoX)
        gotoLayout.addRow("y (mm)",self.gotoY)
        gotoLayout.addRow("z (mm)",self.gotoZ)
        self.gotoX.setRange(-12.5,12.5)
        self.gotoY.setRange(-12.5,12.5)
        self.gotoZ.setRange(-50,50)

        # Set up the form to perform a vertical scan
        self.vertScanButton = QPushButton("Start Vertical Scan")
        self.distanceWidget = QDoubleSpinBox()
        self.stepsWidget = QSpinBox()
        scanLayout.addRow(self.vertScanButton)
        scanLayout.addRow("Distance to Scan",self.distanceWidget)
        scanLayout.addRow("Steps to scan",self.stepsWidget)
        self.distanceWidget.setRange(0,100.0)
        self.stepsWidget.setRange(1,2000)

        # Set up the form for the magnetic field meter
        self.measureButton = QPushButton("Measure Field")
        self.fieldBox = QLabel("reading")
        self.fieldBox.setFrameShape(QFrame.Shape.Box)
        self.fieldBox.setFrameShadow(QFrame.Shadow.Sunken)
        
        #self.fieldSpBox.setRange(-10000,10000)
        meterLayout.addRow(self.measureButton)
        meterLayout.addRow("MagneticField: ",self.fieldBox)

        tabs.addTab(gotoPage,"Go To...")
        tabs.addTab(scanPage, "Vertical Scan")
        tabs.addTab(meterPage,"Magnetic Field")

        self.label = QLabel("Let's get started!")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size: 24px;")
        mainLayout.addWidget(self.label)

        mainLayout.addLayout(graphLayout)
        
        widget.setLayout(mainLayout)

        home_action = QAction("Home all", self)
        home_action.setStatusTip("Homing all stages")
        home_action.triggered.connect(self.homeAll)
        self.toolbar.addAction(home_action)

        goStart_action = QAction("Go to start", self)
        goStart_action.setStatusTip("Going to starting position for scanning")
        goStart_action.triggered.connect(self.goStart)
        self.toolbar.addAction(goStart_action)

        self.gotoButton.setStatusTip("Go to specified position")
        
        self.gotoButton.clicked.connect(self.gotoPosition)

        self.vertScanButton.setStatusTip("Start a Vertical Scan")
        self.vertScanButton.clicked.connect(self.verticalScan)

        self.measureButton.clicked.connect(self.meterButtonClicked)

        self.setStatusBar(self.statusBar())
        
        statusFont = self.statusBar().font()
        statusFont.setPointSize(14)
        self.statusBar().setFont(statusFont)

        # Exit QAction
        file_menu.addAction(QIcon.fromTheme(QIcon.ThemeIcon.ApplicationExit),
                            "Exit", QKeySequence.StandardKey.Quit, self.close)
        
        self.label.setText(meterC.Identify(self.mpSer))
        

    # The following are slot functions that respond to GUI events.
       
    def homeAll(self):
        """Send all stages to home position"""
        stageC.homeAll(self.ser,axes)
        asyncio.run(stageC.readyCheck(self.ser, axes))
        print("All stages homed.")
        self.updatePosition()

    def goStart(self):
        """Move to starting position for scanning"""
        startPos = (0.,0.,50.)
        pulsePos = conv2Pulse(startPos,dist2pulse)
        stageC.gotoPosition(self.ser, pulsePos)
        asyncio.run(stageC.readyCheck(self.ser, axes))
        self.updatePosition()

    def calculatePosition(self) -> list[float, float, float]:
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

    def gotoPosition(self):
        """Move to a specified position in mm"""
        position = (self.gotoX.value(), self.gotoY.value(), self.gotoZ.value())
        pulsePos = conv2Pulse(position,dist2pulse)
        print("Pulse position: ", pulsePos)
        stageC.gotoPosition(self.ser, pulsePos)
        asyncio.run(stageC.readyCheck(self.ser, axes))
        self.updatePosition()

    def verticalScan(self):
        """Scan in vertical direction a set distance with a specified number of steps"""
        distance = self.distanceWidget.value()
        steps = self.stepsWidget.value()
        print("steps = " ,steps)
        stepDistance = distance/steps
        print("step Distance =",stepDistance)
        stepPulses = -int(stepDistance * dist2pulse[2])
        self.statusBar().showMessage("Starting Scan") # This does not work EEB 7/9/2026

        for i in range(steps):
            stageC.moveRelative(self.ser,(0,0,stepPulses))
            asyncio.run(stageC.readyCheck(self.ser, axes))
            self.updatePosition()
            asyncio.run(stageC.readyCheck(self.ser, axes))

    def buttonClicked(self):
        """Handle button click event"""
        print("Button clicked!")
        # You can add more functionality here as needed

    def meterButtonClicked(self):
        """Read Magnetic Field meter when button clicked"""
        field = meterC.fieldMeasure(self.mpSer)
        self.fieldBox.setText(f"{field:.4f}")

        
if __name__ == "__main__":
    app = QApplication([])

    widget = MainWidget()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())