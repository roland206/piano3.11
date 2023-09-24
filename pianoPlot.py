import threading
import time

from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPixmap
from PyQt5.QtWidgets import QWidget, QCheckBox, QFileDialog, QFormLayout, QLabel, QGroupBox, QGridLayout, QPushButton, QHBoxLayout, \
    QVBoxLayout, QSpinBox, QDial, QMenu, QFrame,QComboBox
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QBrush
from PyQt5.QtCore import Qt
from plot import *
import numpy as np
from partiture import Partiture, Note
from midi import Midi, MidiCMD

class pianoPlot(QWidget):
    def __init__(self, setup, ui, takt1, parent = None):
        QWidget.__init__(self, parent)
        self.setup = setup
        self.ui = ui
        self.partiture = setup.partiture
        self.timeStart = self.partiture.taktStart[takt1-1]
        self.timeWindow = 512.0
        self.plotIndex = 0
        self.plotName = ''

        self.violinePixmap = QPixmap("violine.png")
        self.bassPixmap = QPixmap("bass.png")

    def setTakt(self, takt):
        self.timeStart = self.partiture.taktStart[takt - 1]
        self.repaint()
    def setPlotIndex(self, index, text):
        self.plotIndex = index
        self.plotName = text
        self.repaint()
    def mousePressEvent(self, event) -> None:
        event.accept()
        self.lastPos = event.localPos().x()
    def mouseMoveEvent(self, event) -> None:
        event.accept()
        if self.lastPos < 0: return
        newPos = event.localPos().x()
        xMove = -(newPos - self.lastPos) / self.width()
        self.timeStart = max(0, self.timeStart + xMove * self.timeWindow)
        self.lastPos = newPos
        self.repaint()
    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            if self.timeWindow > 128:
                self.timeStart += self.timeWindow * 0.1
                self.timeWindow *= 0.8
        else:
            self.timeStart = max(0, self.timeStart - self.timeWindow * 0.1)
            self.timeWindow *= 1.2
        self.repaint()
    def notenArea(self):
        widget = QWidget()
        policy = widget.sizePolicy()
        policy.setHorizontalStretch(2)
        widget.setSizePolicy(policy)
        return widget

    def drawYTick(self, x0, x1, y, text):
        self.p.drawLine(x0-5, y, x1, y)
        fm = self.fontMetrics()
        self.p.drawText(x0 - 10 - fm.width(text), y + int(0.5 * fm.height()), text)

    def drawTone(self, p, level, x0, x1, y0, h, decay, curve, color):
        pen = QPen(color)
        pen.setWidth(2)
        p.setPen(pen)
        x = np.linspace(x0, x1, max(2, int((x1-x0)/5)), endpoint=True).astype(int)
        y = level/128.0 * np.exp((x0-x)/decay)
        y = y0 - (y * h).astype(int)
        p.drawLine(x[0], y0, x[0], y[0])
        if curve:
            for i in range(len(x)-1):
                p.drawLine(x[i], y[i], x[i+1], y[i+1])
            p.drawLine(x[-1], y[-1], x[-1], y0)
        else:
            p.setBrush(QBrush(color, Qt.SolidPattern))
            p.drawEllipse(x[0]-5,y[0]-10,10,20)

    def buildSoll(self):
        usePedal = self.ui.btnPedal.checkState() and (len(self.ui.pedal.measuredTimes) > 0)
        fm = self.fontMetrics()
        hTotal = self.height()
        xExtra = 80
        xStart = xExtra + 20
        xEnd = self.width() - 20
        tScale = (xEnd - xStart) / self.timeWindow
        mapTime2X = np.polyfit(np.array([self.timeStart, self.timeStart + self.timeWindow]), np.array([xStart, xEnd]), 1)

        self.soll = list(self.setup.partiture.voices)
        self.violineMin, self.violineMax, self.bassMin, self.bassMax = 2, 10, -10, -2
        for t in self.soll + self.ui.gespielt:
            if t.mappedTime > self.timeStart + self.timeWindow : continue
            if t.mappedTime + t.ticks + t.pedalExtension < self.timeStart: continue
            if t.violine:
                self.violineMin, self.violineMax = min(self.violineMin, t.line), max(self.violineMax, t.line)
            else:
                self.bassMin, self.bassMax = min(self.bassMin, t.line), max(self.bassMax, t.line)
        nv = self.violineMax - self.violineMin + 1
        nb = self.bassMax - self.bassMin + 1

        dOben = 15
        dUnten = 6
        dViolineBass = 20
        dPlot = 20 + fm.height()
        if self.plotIndex == 0:
            hPlot, plotSpace = 0,0
        else:
            hPlot = int(hTotal / 8) if self.plotIndex == 1 else int(hTotal / 5)
            plotSpace = hPlot + dPlot

        d = int(float(hTotal - dOben - dViolineBass - dUnten - plotSpace) / float(nv + nb))
        d2 = int(d / 2)
        dSpace = 2
        dl = d - dSpace
        y0Violine = dOben + self.violineMax * d + d2
        y0Bass    = dOben + dViolineBass + (self.bassMax + nv) * d + d2
        y0Plot    = dOben + dViolineBass + dPlot + (nb + nv) * d

        self.p.setBrush(QBrush(QColor(255,255,255)))
        self.p.drawRect(xStart-2-xExtra, dOben- 1, xEnd - xStart + 4 + xExtra, d * nv)
        self.p.drawRect(xStart-2-xExtra, dOben + nv * d + dViolineBass- 1, xEnd - xStart + 4 + xExtra, d * nb)

        if self.plotIndex > 0:
            self.p.drawRect(xStart - 2, y0Plot, xEnd - xStart + 4, hPlot)
            text = self.plotName
            self.p.drawText(int(0.5 * (xStart + xEnd - fm.width(text))), y0Plot - dViolineBass + 5, text)

        if usePedal:
            xListPedal, wListPedal = self.ui.pedal.getPlotRegions(xStart, xEnd, self.timeStart, tScale)
            for i in range(len(xListPedal)):
                self.p.fillRect(xListPedal[i], dOben, wListPedal[i], d * nv - 2, QColor(245,245,245))
                self.p.fillRect(xListPedal[i], dOben + nv * d + dViolineBass, wListPedal[i], d * nb - 2, QColor(245,245,245))
                if self.plotIndex > 0: self.p.fillRect(xListPedal[i], y0Plot, wListPedal[i], hPlot, QColor(245, 245, 245))

        self.p.drawPixmap(xStart+2-xExtra, y0Violine - int(5.5*d), int(1.5*d), 3*d, self.violinePixmap)
        self.p.drawPixmap(xStart+2-xExtra, y0Bass    + int(3.4*d), int(1.4*d), int(1.8*d), self.bassPixmap)

        pen = QPen(QColor(0, 0, 0))
        pen.setWidth(3)
        self.p.setPen(pen)

        for notes in [self.soll, self.ui.gespielt]:
            for note in notes:
                x0 = int(np.polyval(mapTime2X, note.mappedTime - 8))
                if x0 >= xEnd: break
                x1 = int(np.polyval(mapTime2X, note.mappedTime + note.ticks + note.pedalExtension * usePedal + 8))
                if x1 < xStart: continue
                x0, x1 = max(xStart, x0), min(xEnd, x1)
                yLines = []
                line = note.line
                if note.violine:
                    while(line < 1):
                        if (line & 1) == 0: yLines.append(y0Violine - line * d)
                        line += 1
                    while(line > 11):
                        if (line & 1) == 0: yLines.append(y0Violine - line * d)
                        line -= 1
                else:
                    while(line < -11):
                        if (line & 1) == 0: yLines.append(y0Bass - line * d)
                        line += 1
                    while(line > -1):
                        if (line & 1) == 0: yLines.append(y0Bass - line * d)
                        line -= 1
                for y in yLines:
                    self.p.drawLine(x0, y, x1, y)

        for l in range(5):
            y = y0Violine -  2 * d - l * 2 * d
            self.p.drawLine(xStart, y, xEnd, y)
            y = y0Bass + 10 * d - l * 2 * d
            self.p.drawLine(xStart, y, xEnd, y)

        for i, t in enumerate(self.partiture.taktStart):
            x = int(np.polyval(mapTime2X, t))
            if x < xStart-1 or x > xEnd: continue
            self.p.drawLine(x, y0Violine - 2 * d, x, y0Violine - 10 * d)
            if x + 3 + fm.width(str(i+1)) < xEnd:
                self.p.drawText(x + 3, y0Violine - 10 * d - 5, str(i+1))
            self.p.drawLine(x, y0Bass + 10 * d, x, y0Bass + 2 * d)
            if self.plotIndex > 0: self.p.drawLine(x, y0Plot, x, y0Plot + hPlot)

        # [soll] [normal] [pedal]
        # innerhalb [] = violine, bass, unmatched(Violine) unmatched(Bass)
        colorMap = [[QColor(200, 200, 200), QColor(200, 200, 200), QColor(220, 200, 200), QColor(220, 200, 200)],
                    [QColor(200, 240, 200), QColor(200, 200, 240), QColor(255, 100, 100), QColor(255, 100, 100)],
                    [QColor(220, 240, 220), QColor(220, 220, 240), QColor(255, 200, 200), QColor(255, 200, 200)]]

        pen.setWidth(1)
        self.p.setPen(pen)
        modes = [[self.soll, 1, 0, False], [self.ui.gespielt, 0.5, 2, True], [self.ui.gespielt, 0.7, 1, False]]
        for mode in modes:
            if mode[3] and not usePedal: continue
            map = colorMap[mode[2]]
            hNote = int(dl * mode[1])
            for t in mode[0]:
                t0 = t.position - self.timeStart if mode[0] == self.soll else t.mappedTime - self.timeStart
                t1 = t0 + t.ticks
                if mode[3]: t1 += t.pedalExtension
                if t0 >= self.timeWindow or (t1 < 0): continue
                t0, t1 = max(0.0 ,t0), min(t1, self.timeWindow)
                x = xStart + int(t0 * tScale)
                yCenter = y0Violine - d * t.line if t.violine else y0Bass - d * t.line
                y = int(yCenter - hNote/2)
                wx = int((t1-t0) * tScale) + 1
                self.p.setBrush(QBrush(map[t.getColor()]))
                self.p.drawRoundedRect(x, y, wx, hNote, 10, 10)
                if t.kreuz and (x+10) < xEnd: self.p.drawText(x, yCenter + 5, '#')

        if self.plotIndex == 3:# male speed
            speedData = self.ui.speedData
            if speedData['valid']:
                map = np.polyfit(np.array([0, max(1.2, speedData['max'])]), np.array([y0Plot + hPlot, y0Plot]), 1)
                speed = speedData['data']
                speedY = np.polyval(map, speed).astype(int)
                timesX = np.polyval(mapTime2X, speedData['times']).astype(int)

                mean = speedData['mean']
                sollSpeedY = int(np.polyval(map, 1.0))
                meanSpeedY = int(np.polyval(map, mean))

                self.p.setPen(QPen(Qt.darkGreen, 3, Qt.DashLine))
                self.drawYTick(xStart, xEnd, sollSpeedY, f'{self.partiture.bpm} bmp')

                self.p.setPen(QPen(Qt.blue, 2, Qt.DashLine))
                if abs(sollSpeedY - meanSpeedY) < 20:
                    meanSpeedY = sollSpeedY - 20 * np.sign(sollSpeedY - meanSpeedY)
                self.drawYTick(xStart, xEnd, meanSpeedY, f'{(mean * self.partiture.bpm):.1f} bmp')

                self.p.setPen(QPen(Qt.red, 2))

                for i in range(len(timesX) - 1):
                    if timesX[i] < xStart or timesX[i+1] > xEnd: continue
                    if speed[i] < 0  or speed[i+1] < 0: continue
                    self.p.drawLine(timesX[i], speedY[i], timesX[i+1], speedY[i + 1])
        elif self.plotIndex == 4:
            time,legato, color = [], [], []
            for note in self.ui.gespielt:
                if note.legato is not None:
                    time.append(note.mappedTime)
                    legato.append(note.legato)
                    color.append(note.getColor())
            if len(time) > 0:
                x = np.polyval(mapTime2X, np.array(time)).astype(int)
                legato = np.array(legato)
                lmin = np.min(legato)
                lmax = np.max(legato)
                map = np.polyfit(np.array([lmin, lmax]), np.array([y0Plot + hPlot - 10, y0Plot + 10]), 1)
                y = np.polyval(map, legato).astype(int)

                self.p.setPen(QPen(Qt.darkGray, 1, Qt.DashLine))
                yBase = int(np.polyval(map, 0))

                step = 10000
                while int((lmax-lmin) / step) < 3: step /= 10
                if int((lmax-lmin) / step) > 10: step *= 5
                if int((lmax-lmin) / step) > 6:  step *= 2
                base = step * int(lmin / step)
                while(base < lmax):
                    if base > lmin:
                        self.drawYTick(xStart, xEnd, int(np.polyval(map, base)), f'{base:.0f}')
                    base += step
                self.p.setPen(QPen(Qt.black, 2, Qt.SolidLine))
                self.p.drawLine(xStart, yBase, xEnd, yBase)
                for i, x in enumerate(x):
                    if x >= xEnd or x < xStart: continue
                    self.p.drawLine(x, yBase, x, y[i])
                    self.p.setBrush(QBrush(colorMap[1][color[i]], Qt.SolidPattern))
                    self.p.drawEllipse(x - 5, y[i] - 10, 10, 20)
        elif self.plotIndex == 2:
            mapLevel2Y = np.polyfit(np.array([0, 128]), np.array([y0Plot + hPlot, y0Plot]), 1)

            names = ['pp', 'p', 'mf', 'f', 'ff']
            self.p.setPen(QPen(Qt.black, 1, Qt.DashLine))
            for i, tick in enumerate(names):
                y = int(np.polyval(mapLevel2Y, 128 * (i+0.5) / (len(names))))
                self.drawYTick(xStart, xEnd, y, tick)

            y0 = y0Plot + hPlot
            for t in self.ui.gespielt:
                x = int(np.polyval(mapTime2X, t.mappedTime))
                if x < xStart or x > xEnd: continue
                color = colorMap[1][t.getColor()]
                y = int(np.polyval(mapLevel2Y, t.level))
                self.p.setPen(QPen(Qt.black))
                self.p.drawLine(x, y0, x, y)
                self.p.setBrush(QBrush(color, Qt.SolidPattern))
                self.p.drawEllipse(x - 5, y - 10, 10, 20)

        elif self.plotIndex == 1:
            mapLevel2Y = np.polyfit(np.array([-3, 131]), np.array([y0Plot + hPlot, y0Plot]), 1)
            x = np.polyval(mapTime2X, self.ui.pedal.mappedTimes).astype(int)
            y = np.polyval(mapLevel2Y, self.ui.pedal.level).astype(int)
            for i in range(len(x)-1):
                if x[i] > xEnd or x[i+1] < xStart: continue
                self.p.drawLine(x[i], y[i], x[i+1], y[i])
                self.p.drawLine(x[i+1], y[i], x[i+1], y[i+1])

        elif self.plotIndex > 0:
            for t in self.ui.gespielt:
                t0 = t.mappedTime - self.timeStart
                if t0 < 0: continue
                t1 = t0 + t.ticks + t.pedalExtension
                if t0 >= self.timeWindow or (t1 < 0): continue
                t1 = min(t1, self.timeWindow)
                x0 = xStart + int(t0 * tScale)
                x1 = xStart + int(t1 * tScale)
                self.drawTone(self.p, t.level, x0, x1, y0Plot + hPlot, hPlot,50*tScale, self.plotIndex==1, colorMap[1][t.getColor()])


    def paintEvent(self, event):
        self.p = QPainter(self)
        self.p.setRenderHint(QPainter.Antialiasing)
        self.p.setBrush(QBrush(QColor(230,230,230)))
        self.p.drawRect(0, 0, self.width(), self.height())
        self.buildSoll()
        self.p.end()

