
from PySide6.QtWidgets import QLabel

class numDisplay(QLabel):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("""
                           border: 3px solid darkblue;
                           border-style: inset;
                           text-align: center;
                           font-size: 18px;
                           height: 22px;
                           """)
        
    def setValue(self,num):
        self.setText(f"{num}")