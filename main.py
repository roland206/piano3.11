from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QCheckBox, QFormLayout, QTabWidget
import sys
from pianoUI import pianoUI
from setup import Setup

class MainWindow(QTabWidget):
    def __init__(self, setup):
        super(MainWindow, self).__init__()
        self.addTab(pianoUI(setup), "Teaching")

        self.currentChanged.connect(self.chanced)
        self.resize(2800, 1800)

    def chanced(self):
        print(f"Sollte re-read {self.currentIndex()}")


def main():

    setup = Setup()
    app = QApplication(sys.argv)
    main = MainWindow(setup)
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':

    main()