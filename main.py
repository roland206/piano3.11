from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QCheckBox, QFormLayout, QTabWidget
import sys
from pianoUI import pianoUI
from setupUI import setupUI
from setup import Setup

class MainWindow(QTabWidget):
    def __init__(self, setup):
        super(MainWindow, self).__init__()
        self.addTab(pianoUI(setup), "Main")
        self.addTab(setupUI(setup), "Setup")

        self.resize(2800, 1800)

def main():

    setup = Setup()
    app = QApplication(sys.argv)
    main = MainWindow(setup)
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':

    main()