import sys
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QApplication
from numDisplay import numDisplay

class MainWidget(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Test numDisplay class")
        
        self.myNum = numDisplay()
        w = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.myNum)
        w.setLayout(layout)
        self.setCentralWidget(w)
        self.myNum.setValue(43.2)

app = QApplication(sys.argv)
window = MainWidget()
window.show()
app.exec()
