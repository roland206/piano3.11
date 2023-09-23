import time
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QBrush
from PyQt5.QtWidgets import QWidget, QCheckBox, QFormLayout, QLabel, QGroupBox, QGridLayout, QPushButton, QHBoxLayout, \
    QVBoxLayout, QDial, QMenu, QFrame, QFileDialog
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QBrush
from PyQt5.QtCore import Qt
from partiture import Partiture

class setupUI(QWidget):
    def __init__(self, setup, parent = None):
        QWidget.__init__(self, parent)

        self.setup = setup
        layout = QHBoxLayout()
        self.setLayout(layout)

        loadMuse = QPushButton('Lade MuseScore Partiture')
        loadMuse.clicked.connect(self.loadMuse)
        layout.addWidget(loadMuse)


    def loadMuse(self):
        fname, x = QFileDialog.getOpenFileName(self, 'Lade MuseScore Datei', '', 'MuseScore XML (*.mscx);;Projekt (*.part)')
        if fname:
            if x == 'MuseScore XML (*.mscx)':
                self.setup.set('partitureFile', fname)
                self.setup.partiture = Partiture(self.setup.getStr('partitureFile'))
                self.setup.filename = fname.replace('.mscx', '.part')
                self.setup.save()
                print(f'Load MuseScore {fname}')
            else:
                self.setup.load(fname)
                print(f'Lade Project {fname}')
