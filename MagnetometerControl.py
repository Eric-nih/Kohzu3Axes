# Python GUI for controlling stages and magnetic field meter

import sys, serial
import time

import stageCommands as stageC
from numDisplay import numDisplay
import meterCommands as meterC
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QToolBar, QHBoxLayout,
    QFormLayout,QVBoxLayout, QWidget, QPushButton, QDoubleSpinBox, QSpinBox, 
    QTabWidget, QGridLayout, QSpacerItem, QSizePolicy, QTableView,
    QHeaderView, QFileDialog, QComboBox
)
from PySide6.QtGui import QIcon, QKeySequence, QAction
from PySide6.QtCore import (Qt, QAbstractTableModel, QThreadPool,QRunnable,
                            QObject, Signal, Slot)
from pandas import DataFrame

# if the Magnetic field meter is connected, set this to True
MeterConnected = False
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

def calculatePosition(controller) -> list[float, float, float]:
    """Calculate the current position of the stages in mm, returning a list"""
    Positions = [0.,0.,0.]
    for a in axes:
        Positions[a-1] = stageC.readPos(controller,a)/dist2pulse[a-1]
        # print("Position of axis ", a, " = ", Positions[a-1], " mm")
    return Positions
 
class TableModel(QAbstractTableModel):
    """This class sets up a view used by the GUI to display a table model"""
    def __init__(self, data):
        super().__init__()
        self._data = data
        #self.ser = serial

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        return self._data.shape[1]

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])

            if orientation == Qt.Vertical:
                return str(self._data.index[section])
            
# adding multithreading to show table as a scan runs
class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    - row_added: Emits (row_index, list_of_cell_data) when a row is generated.
    - finished: Emits when the background subroutine completes.
    """
    row_added = Signal(int, list)
    finished = Signal()

class VertScanWorker(QRunnable):
    """
    Worker thread that runs a background subroutine.
    This class produces a separate thread for vertical scans
    """
    def __init__(self, serial, parameters):
        super().__init__()
        self.ser = serial[0]
        self.mpSer = serial[1]
        self.parameters = parameters
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        # setup data table parameters

        distance = self.parameters[0]
        steps = self.parameters[1]

        # print("steps = " ,steps)
        stepDistance = distance/steps
        # print("step Distance =",stepDistance)
        stepPulses = -int(stepDistance * dist2pulse[2])

        dtypes = {
            'time': 'string',
            'X': 'float64',
            'Y': 'float64',
            'Z': 'float64',
            'Field': 'float64',
            'Units': 'string'
        }

            
        # we need to get initial data before moving stages
        position = calculatePosition(self.ser)
        currentTime = time.asctime()
        if MeterConnected:
            units = meterC.getUnits(self.mpSer)
            field = meterC.fieldMeasure(self.mpSer)
        else:
            units = "Not Connected"
            field = float('nan')
        dataList = [currentTime,position[0],position[1],position[2],field,units]

        # Emit a dataList of location, time, and magnetic field
        self.signals.row_added.emit(0,dataList)

        #self.data.loc[0] = dataList

        for i in range(1,steps+1):
            stageC.moveRelative(self.ser,(0,0,stepPulses))
            position = calculatePosition(self.ser)
            currentTime = time.asctime()
            if MeterConnected:
                units = meterC.getUnits(self.mpSer)
                field = meterC.fieldMeasure(self.mpSer)
            else:
                units = "not connected"
                field = float('nan')
            dataList = [currentTime,position[0],position[1],position[2],field,units]
            # Emit the data back to the main thread safely
            self.signals.row_added.emit(i, dataList)
            
        # Signal that the entire work process is finished
        self.signals.finished.emit()


class Scan3DWorker(QRunnable):
    """ This class produces a separate thread to run a 3D Scan"""

    def __init__(self, serial, parameters):
        super().__init__()
        self.ser = serial[0]
        self.mpSer = serial[1]
        self.par = parameters  # change parameters to a dictionary  EEB 9/8/2026
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
 
        # setup data table parameters
        dtypes = {
            'time': 'string',
            'X': 'float64',
            'Y': 'float64',
            'Z': 'float64',
            'Field': 'float64',
            'Units': 'string'
        }

        

        self.data = DataFrame(index=range((self.par["xSteps"]+1)*(self.par["ySteps"]+1)*
                                          (self.par["zSteps"]+1)),
                                            columns=dtypes.keys()).astype(dtypes)
        # self.model = TableModel(self.data)
        # self.dataTable.setModel(self.model)

        for z in range(0,self.par["zSteps"]+1):
            newPos = conv2Pulse((self.par["xStart"],self.par["yStart"],self.par["zStart"]
                                 +z*self.par["zStepDistance"]),dist2pulse)
            stageC.gotoPosition(self.ser,newPos)
            print((self.par["xStart"],self.par["yStart"],self.par["zStart"]
                   -z*self.par["zStepDistance"]))

            for x in range(0,self.par["xSteps"] + 1):
                newPos = conv2Pulse((self.par["xStart"]+x*self.par["xStepDistance"],
                                     self.par["yStart"],self.par["zStart"]
                                     -z*self.par["zStepDistance"]),dist2pulse)
                stageC.gotoPosition(self.ser,newPos)
                print((self.par["xStart"]+x*self.par["xStepDistance"]
                       ,self.par["yStart"],self.par["zStart"]
                       +z*self.par["zStepDistance"]))

                for y in range(0,self.par["ySteps"] + 1):
                    newPos = conv2Pulse((self.par["xStart"]+x*self.par["xStepDistance"],
                                         self.par["yStart"]+y*self.par["yStepDistance"],
                                        self.par["zStart"]-z*self.par["zStepDistance"]),dist2pulse)
                    stageC.gotoPosition(self.ser,newPos)

                    position = calculatePosition(self.ser)
                    currentTime = time.asctime()
                    if MeterConnected:
                        units = meterC.getUnits(self.mpSer)
                        field = meterC.fieldMeasure(self.mpSer)
                    else:
                        units = "not connected"
                        field = float('nan')
                    dataList = [currentTime,position[0],position[1],position[2],field,units]
                    index = x + y*(self.par["xSteps"]+1) + z*(self.par["xSteps"]+1)*(
                        self.par["ySteps"]+1)

                    # Emit the data back to the main thread safely
                    self.signals.row_added.emit(index, dataList)

        # Signal that the entire work process is finished
        self.signals.finished.emit()


                    # self.data.loc[index] = dataList
                    # self.dataTable.update()
                    # self.dataTable.resizeColumnsToContents()


class MainWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Magnetic Field Measurement")
        self.setMinimumSize(900,200)
        self.setWindowIcon(QIcon("resources\\magnet--arrow.png"))

        # Initialize controller
        self.ser = serial.Serial('com6', 38400,8,"N",1,timeout=1)
        print("Opening Connection to controller")
        self.statusBar().showMessage("Connected to controller")

        if MeterConnected:
            self.mpSer = serial.Serial('Com5',115200,8,"N",1,timeout=1)
            print("Opening connection to meter")
        else:
            self.mpSer = None

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
        scan3DPage = QWidget(self)
        scan3DLayout = QFormLayout()
        scan3DPage.setLayout(scan3DLayout)

        mainLayout.addWidget(tabs,2)

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

        # Set up the form for a 3D scan
        self.Scan3DButton = QPushButton("Start a 3D scan")
        self.xStartWidget = QDoubleSpinBox() # x position to start from
        self.yStartWidget = QDoubleSpinBox() # y position to start from
        self.zStartWidget = QDoubleSpinBox() # z position to start from
        self.xDistWidget = QDoubleSpinBox() # x distance to scan
        self.yDistWidget = QDoubleSpinBox() # y distance to scan
        self.zDistWidget = QDoubleSpinBox() # z distance to scan
        self.xStepsWidget = QSpinBox() # how many points in x
        self.yStepsWidget = QSpinBox() # how many points in y
        self.zStepsWidget = QSpinBox() # how many points in z
        scan3DLayout.addRow(self.Scan3DButton)
        scan3DLayout.addRow("Start position in x",self.xStartWidget)
        scan3DLayout.addRow("X Scan Distance",self.xDistWidget)
        scan3DLayout.addRow("X steps",self.xStepsWidget)
        scan3DLayout.addRow("Start position in y", self.yStartWidget)
        scan3DLayout.addRow("Y Scan Distance",self.yDistWidget)
        scan3DLayout.addRow("Y steps",self.yStepsWidget)
        scan3DLayout.addRow("Start position in z", self.zStartWidget)
        scan3DLayout.addRow("Z Scan Distance",self.zDistWidget)
        scan3DLayout.addRow("Z steps",self.zStepsWidget)
        self.zDistWidget.setRange(0,100.0)
        self.xDistWidget.setRange(0,25.0)
        self.yDistWidget.setRange(0,25.0)
        self.xStartWidget.setRange(-12.5,12.5)
        self.yStartWidget.setRange(-12.5,12.5)
        self.zStartWidget.setRange(-50.0,50.50)
        self.xStartWidget.setValue(-12.5)
        self.yStartWidget.setValue(-12.5)
        self.zStartWidget.setValue(50.0)

        # Set up the form for the magnetic field meter
        self.measureButton = QPushButton("Measure Field")
        self.setUnits = QComboBox()
        self.fieldNum = numDisplay()
        self.unitsLabel = QLabel()

        self.setUnits.addItems(["Gauss","Tesla","Oersted","A/cm"])
        
        meterLayout.addRow(self.measureButton)
        meterLayout.addRow("Field Units:",self.setUnits)
        measureLayout = QHBoxLayout()
        measureLayout.addWidget(self.fieldNum)
        measureLayout.addWidget(self.unitsLabel)
        meterLayout.addRow("Magnetic Field: ",measureLayout)

        tabs.addTab(gotoPage,"Go To...")
        tabs.addTab(meterPage,"Magnetic Field")
        tabs.addTab(scanPage, "Vertical Scan")
        tabs.addTab(scan3DPage, "3D Scan")
   
        # set up central panel display latest positions and measurements
        self.centerLayout = QGridLayout()

        self.xPos = numDisplay()
        self.yPos = numDisplay()
        self.zPos = numDisplay()
        self.fieldDisplay = numDisplay()
        self.unitsLabel2 = QLabel()
        self.centerLayout.addWidget(QLabel("X (mm)",alignment=Qt.AlignHCenter),0,0)
        self.centerLayout.addWidget(self.xPos,1,0)
        self.centerLayout.addWidget(QLabel("Y (mm)",alignment=Qt.AlignHCenter),0,1)
        self.centerLayout.addWidget(self.yPos,1,1)
        self.centerLayout.addWidget(QLabel("Z (mm)",alignment=Qt.AlignHCenter),0,2)
        self.centerLayout.addWidget(self.zPos,1,2)
        self.centerLayout.addWidget(QLabel("Magnetic Field",alignment=Qt.AlignRight|Qt.AlignVCenter),2,0)
        self.centerLayout.addWidget(self.fieldDisplay,2,1)
        self.centerLayout.addWidget(self.unitsLabel2,2,2)

        for column in range(self.centerLayout.columnCount()):
            self.centerLayout.setColumnStretch(column,1)

        spacer = QSpacerItem(0,20,QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
        self.centerLayout.addItem(spacer,3,0)
        centerWidget = QWidget(self)
        centerWidget.setLayout(self.centerLayout)
        mainLayout.addWidget(centerWidget,1)

        # Set up and display table of measurements. 

        self.dataTable = QTableView()
        graphLayout.addWidget(self.dataTable)
        graphWidget = QWidget()
        graphWidget.setLayout(graphLayout)
        mainLayout.addWidget(graphWidget,3)
        
        widget.setLayout(mainLayout)
        #print("set the main layout")
        home_action = QAction("Home all", self)
        home_action.setStatusTip("Homing all stages")
        home_action.triggered.connect(self.homeAll)
        self.toolbar.addAction(home_action)

        goStart_action = QAction("Go to start", self)
        goStart_action.setStatusTip("Going to starting position for scanning")
        goStart_action.triggered.connect(self.goStart)
        self.toolbar.addAction(goStart_action)

        save_action = QAction("Save data", self)
        save_action.setStatusTip("Save data from a scan to a CSV file")
        save_action.triggered.connect(self.saveData)
        self.toolbar.addAction(save_action)

        self.gotoButton.setStatusTip("Go to specified position")
        
        self.gotoButton.clicked.connect(self.gotoPosition)

        self.vertScanButton.setStatusTip("Start a Vertical Scan")
        self.vertScanButton.clicked.connect(self.verticalScan)

        self.Scan3DButton.clicked.connect(self.scan3D)
        self.Scan3DButton.setStatusTip("Start a 3D scan")

        self.measureButton.clicked.connect(self.meterButtonClicked)
        self.setUnits.currentIndexChanged.connect(self.chooseUnits)

        self.setStatusBar(self.statusBar())
        
        statusFont = self.statusBar().font()
        statusFont.setPointSize(14)
        self.statusBar().setFont(statusFont)

        # Exit QAction
        file_menu.addAction(QIcon.fromTheme(QIcon.ThemeIcon.ApplicationExit),
                            "Exit", QKeySequence.StandardKey.Quit, self.close)
        
        # set up data frame for scans
        currentTime = time.asctime()
        self.data = DataFrame([
            [currentTime, 0.0,0.0,0.0,0.0,"units"],
                   
                ], columns = ['Time','X', 'Y', 'Z','field', 'units' ])
        
        self.model = TableModel(self.data)
        self.dataTable.setModel(self.model)
        self.dataTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        # Global QThreadPool instance
        self.threadpool = QThreadPool.globalInstance()


    # The following are slot functions that respond to GUI events.

    @Slot()   
    def homeAll(self):
        """Send all stages to home position"""
        stageC.homeAll(self.ser,axes)
        print("All stages homed.")
        self.updatePosition()

    @Slot()
    def goStart(self):
        """Move to starting position for scanning"""
        startPos = (0.,0.,50.)
        pulsePos = conv2Pulse(startPos,dist2pulse)
        stageC.gotoPosition(self.ser, pulsePos)
        self.updatePosition()

    @Slot()
    def updatePosition(self):
        """Update the label with the current position of the stages"""
        #self.label.setText("current position: " + str(calculatePosition(self.ser)))
        position = calculatePosition(self.ser)
        self.xPos.setValue(position[0])
        self.yPos.setValue(position[1])
        self.zPos.setValue(position[2])

    @Slot()
    def gotoPosition(self):
        """Move to a specified position in mm"""
        position = (self.gotoX.value(), self.gotoY.value(), self.gotoZ.value())
        pulsePos = conv2Pulse(position,dist2pulse)
        #print("Pulse position: ", pulsePos)
        stageC.gotoPosition(self.ser, pulsePos)
        self.updatePosition()
        self.updateMeasurement()

    @Slot()
    def verticalScan(self):
        """Scan in vertical direction a set distance with a specified number of steps"""
        distance = self.distanceWidget.value()
        steps = self.stepsWidget.value()

        dtypes = {
            'time': 'string',
            'X': 'float64',
            'Y': 'float64',
            'Z': 'float64',
            'Field': 'float64',
            'Units': 'string'
        }
        
        self.data = DataFrame(index=range(steps+1),columns=dtypes.keys()).astype(dtypes)
        self.model = TableModel(self.data)
        self.dataTable.setModel(self.model)

        self.updateStatus("Starting z Scan")

        serial = (self.ser, self.mpSer) 

        worker = VertScanWorker(serial,(distance,steps))
        worker.signals.row_added.connect(self.on_row_added)
        worker.signals.finished.connect(self.on_process_finished)

        # Start worker thread inside the thread pool
        self.threadpool.start(worker)

        
    @Slot()
    def scan3D(self):
        """Scan magnetic field in 3 dimensions (x,y,z)"""
        # I need starting position as well
        xStart = self.xStartWidget.value()
        xDistance = self.xDistWidget.value()
        xSteps = self.xStepsWidget.value()
        yStart = self.yStartWidget.value()
        yDistance = self.yDistWidget.value()
        ySteps = self.yStepsWidget.value()
        zStart = self.zStartWidget.value()
        zDistance = self.zDistWidget.value()
        zSteps = self.zStepsWidget.value()
        
        xStepDistance = xDistance/xSteps
        yStepDistance = yDistance/ySteps
        zStepDistance = zDistance/zSteps

        parameters = {"xSteps": xSteps, "ySteps": ySteps, "zSteps": zSteps,
                      "xStart": xStart, "yStart": yStart, "zStart": zStart,
                      "xStepDistance": xStepDistance, "yStepDistance": yStepDistance,
                      "zStepDistance": zStepDistance}
        
        self.updateStatus("Starting 3D Scan")

        # setup data table parameters
        dtypes = {
            'time': 'string',
            'X': 'float64',
            'Y': 'float64',
            'Z': 'float64',
            'Field': 'float64',
            'Units': 'string'
        }

        self.data = DataFrame(index=range((xSteps+1)*(ySteps+1)*(zSteps+1)),
                              columns=dtypes.keys()).astype(dtypes)
        self.model = TableModel(self.data)
        self.dataTable.setModel(self.model)

        serial = (self.ser, self.mpSer)

        worker = Scan3DWorker(serial,parameters)
        worker.signals.row_added.connect(self.on_row_added)
        worker.signals.finished.connect(self.on_process_finished)

        # Start worker thread inside the thread pool
        self.threadpool.start(worker)

        # for z in range(0,zSteps+1):
        #     newPos = conv2Pulse((xStart,yStart,zStart+z*zStepDistance),dist2pulse)
        #     stageC.gotoPosition(self.ser,newPos)
        #     print((xStart,yStart,zStart-z*zStepDistance))

        #     for x in range(0,xSteps + 1):
        #         newPos = conv2Pulse((xStart+x*xStepDistance,yStart,zStart-z*zStepDistance),dist2pulse)
        #         stageC.gotoPosition(self.ser,newPos)
        #         print((xStart+x*xStepDistance,yStart,zStart+z*zStepDistance))

        #         for y in range(0,ySteps + 1):
        #             newPos = conv2Pulse((xStart+x*xStepDistance,yStart+y*yStepDistance,
        #                                           zStart-z*zStepDistance),dist2pulse)
        #             stageC.gotoPosition(self.ser,newPos)

        #             position = calculatePosition(self.ser)
        #             currentTime = time.asctime()
        #             if MeterConnected:
        #                 units = meterC.getUnits(self.mpSer)
        #                 field = meterC.fieldMeasure(self.mpSer)
        #             else:
        #                 units = "not connected"
        #                 field = float('nan')
        #             dataList = [currentTime,position[0],position[1],position[2],field,units]
        #             index = x + y*(xSteps+1)+ z*(xSteps+1)*(ySteps+1)

        # self.updateStatus("Finished 3D scan")


    @Slot()
    def buttonClicked(self):
        """Handle button click event"""
        print("Button clicked!")
        # You can add more functionality here as needed

    @Slot()
    def meterButtonClicked(self):
        """Read Magnetic Field meter when button clicked"""
        field = meterC.fieldMeasure(self.mpSer)
        
        self.fieldNum.setValue(field)
        self.fieldDisplay.setValue(field)
        units = meterC.getUnits(self.mpSer)
        #print("field Units: ",units)
        self.unitsLabel.setText(units)
        self.updateMeasurement()
        self.updatePosition()

    @Slot()
    def updateMeasurement(self):
        """Read Magnetic Field meter for scans"""
        units = meterC.getUnits(self.mpSer)
        field = meterC.fieldMeasure(self.mpSer)
        self.unitsLabel2.setText(units)
        self.fieldDisplay.setValue(field)

    @Slot()
    def saveData(self):
        """Save data collected from a scan to a CSV file"""
        # open a file dialog
        filename = QFileDialog.getSaveFileName(self,caption="Save data to: ",filter="CSV file (*.csv)")[0]
        print("File = ",filename)
        #print(type(filename))
        self.data.to_csv(filename)
        print("File was saved")

    @Slot(int)
    def chooseUnits(self,index):
        """Select the units to measure magnetic field in"""
        # order of units: ["Gauss","Tesla","Oersted","A/cm"]
        match index:
            case 0:
                meterC.setUnits(self.mpSer,"GAUS")
            case 1:
                meterC.setUnits(self.mpSer,"TESL")
            case 2:
                meterC.setUnits(self.mpSer,"OERS")
            case 3:
                meterC.setUnits(self.mpSer,"AM")

    @Slot(int,list)
    def on_row_added(self, row_index, data):
        # Update row dynamically at row_index
        self.data.loc[row_index] = data
        self.dataTable.update()
        self.dataTable.resizeColumnsToContents()

    @Slot()
    def on_process_finished(self):
       self.statusBar().showMessage("Scan Finished")

    @Slot(str)
    def updateStatus(self,message):
        self.statusBar().showMessage(message)


        
if __name__ == "__main__":
    app = QApplication([])

    widget = MainWidget()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())