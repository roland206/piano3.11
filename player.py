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

class player(QWidget):
    def __init__(self, setup, parent = None):
        QWidget.__init__(self, parent)
        self.gespielt = []
        self.pedal = Pedal()
        self.midi = Midi(1, self)
        self.lastPos = -1
        self.tachos = []
        self.setup = setup
        self.partiture = setup.partiture
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.notenWidget = self.notenArea()
        layout.addWidget(self.notenWidget, stretch=5)
        layout.addWidget(self.controlArea(), stretch=1)


        takt1 = setup.getInt('ersterTakt')
        self.timeStart = self.partiture.taktStart[takt1-1]
        self.timeWindow = 512.0
        self.plotIndex = 0
        self.lastMIDIfilename = 'lastMIDI.text'

        self.speedData = {'valid': False}
        self.legatoData = {'valid': False}

        self.violinePixmap = QPixmap("violine.png")
        self.bassPixmap = QPixmap("bass.png")

    def saveMIDIData(self, cmds, times):
        if (len(cmds) > 0):
            with open(self.lastMIDIfilename, 'w') as f:
                i = 0
                for cmd in cmds:
                    f.write(f'{cmd[0]}:{cmd[1]}:{cmd[2]}:{times[i]}\n')
                    i += 1
    def loadMIDIData(self):
        with open(self.lastMIDIfilename) as f:
            lines = f.readlines()
            cmds, times = [], []
            for line in lines:
                data = line.split(':')
                cmds.append([int(data[0]), int(data[1]), int(data[2])])
                times.append(float(data[3]))
        self.bufferFull(cmds, times)
    def bufferFull(self, cmds, times):
        self.saveMIDIData(cmds, times)
        keyTime, keyLevel, self.gespielt = [], [], []
        self.pedal = Pedal()
        self.sec2ticks = self.setup.getFloat('bpm') * 64.0 / 60
        self.ticks2sec = 1.0 / self.sec2ticks
        for i in range(188):
            keyTime.append(0.0)
            keyLevel.append(0)
        for i, cmd in enumerate(cmds):
            if False:
                if cmd[0] == 176: print(f'{times[i]:.3f} Pedal pressure {cmd[2]}')
                if cmd[0] == 144: print(f'{times[i]:.3f} Key pressed    {cmd[1]}')
                if cmd[0] == 128: print(f'{times[i]:.3f} Key released   {cmd[1]}')
            t = times[i] * self.sec2ticks
            key = cmd[1]
            if cmd[0] == 144:
                keyTime[key] = t
                keyLevel[key] = cmd[2]
            elif cmd[0] == 128:
                note = Note(key, t - keyTime[key] , keyTime[key], 0, True, level = keyLevel[key])
                note.violine = note.line >= self.violineMin
                self.gespielt.append(note)
            elif cmd[0] == 176 and key == 64: self.pedal.add(t, cmd[2])
        if len(self.gespielt) > 0:
            t0 = self.gespielt[0].position
            for note in self.gespielt:
                note.position -= t0
            self.pedal.adjustMeasuredTimes(-t0)
        self.superMatcher()
        self.repaint()
    def simulation(self):
        self.gespielt = []
        self.sec2ticks = self.setup.getFloat('bpm') * 64.0 / 60
        self.ticks2sec = 1.0 / self.sec2ticks

        if True:
            self.repaint()
            return
        tLast = 0
        self.pedal = Pedal()
        self.pedal.add(tLast, False)
        for t in self.partiture.taktStart:
            self.pedal.add((t+tLast+4)/2, False)
            self.pedal.add((t + tLast + 12)/2, True)
            self.pedal.add(t+2, False)
            self.pedal.add(t + 6, True)
            tLast = t
        self.pedal.add(t+8, False)

        for note in self.soll:
            if np.random.normal(0, 1) > 2: continue
            tastError = 2 if np.random.normal(0, 1) >= 2 else 0
            pos   = np.random.normal(note.position * 0.8, 8)
            ticks = max(10, np.random.normal(note.ticks, 5))
            level = 30 + int(np.random.random() * 30)
            n = Note(note.taste + tastError, int(ticks), pos, 0, note.violine, level)
            self.gespielt.append(n)



 #               self.pedal.add(t, cmd[2] > 0)
        self.superMatcher()
        self.repaint()
    def spinArea(self, label, xmin, xmax, value, function):
        me = QWidget()
        layout = QHBoxLayout()
        me.setLayout(layout)
        layout.addWidget(QLabel(label))
        spinBox = QSpinBox()
        spinBox.setRange(xmin, xmax)
        spinBox.setValue(value)
        spinBox.valueChanged.connect(function)
        layout.addWidget(spinBox)
        return me, spinBox
    def setSpeed(self):
        self.setup.set('bpm', self.speedSpinBox.value())
        self.repaint()
    def plotIndexChange(self, i):
        self.plotIndex = i
        self.repaint()
    def setFirst(self):
        takt = self.firstSpinBox.value()
        self.setup.set('ersterTakt', takt)
        self.timeStart = self.partiture.taktStart[takt-1]
        self.repaint()
    def loadMuse(self):
        fname, x = QFileDialog.getOpenFileName(self, 'Lade MuseScore Datei', '', 'MuseScore XML (*.mscx);;Projekt (*.part)')
        if fname:
            if x == 'MuseScore XML (*.mscx)':
                self.setup.set('partitureFile', fname)
                self.setup.partiture = Partiture(self.setup.getStr('partitureFile'))
                self.setup.filename = fname.replace('.mscx', '.part')
                self.setup.save()
            else:
                self.setup.load(fname)
            self.gespielt = []
            self.pedal = Pedal()

    def monitorWidget(self):
        widget = QWidget()
        layout = QHBoxLayout()
        widget.setLayout(layout)
        self.rubatoTacho = Tacho('Rubato *64.tel', 0, 20, 5, '{value:.0f}')
        self.tempoTacho = Tacho('Tempo *bpm', 40, 10 * int(self.partiture.bpm/10) + 20, 10, '{value:.0f}')
        self.legatoTacho = Tacho('Legato *msec', -1000, 1000 , 250, '{value:.0f}')
        layout.addWidget(self.rubatoTacho)
        layout.addWidget(self.tempoTacho)
        layout.addWidget(self.legatoTacho)
        return widget

    def controlArea(self):
        me = QWidget()
        topLayout = QHBoxLayout()
        me.setLayout(topLayout)

        buttonWidget = QWidget()
        buttonLayout = QHBoxLayout()
        buttonWidget.setLayout(buttonLayout)

        ctlWidget = QWidget()
        ctlLayout = QVBoxLayout()
        ctlWidget.setLayout(ctlLayout)
        buttonLayout.addWidget(ctlWidget, stretch = 1)
        buttonLayout.addWidget(self.monitorWidget(), stretch = 3)

        loadMuse = QPushButton('Lade MuseScore Partitur')
        loadMuse.clicked.connect(self.loadMuse)
        ctlLayout.addWidget(loadMuse)

        btnLayout = QHBoxLayout()
        btnWidget = QWidget()
        btnWidget.setLayout(btnLayout)
        ctlLayout.addWidget(btnWidget)

        btn = QPushButton('Abspielen')
        btn.clicked.connect(self.abspielen)
        btnLayout.addWidget(btn)

        btn = QPushButton('Wiederholen')
        btn.clicked.connect(self.wiederholen)
        btnLayout.addWidget(btn)

        btn = QPushButton('Simulation')
        btn.clicked.connect(self.simulation)
        btnLayout.addWidget(btn)

        btn = QPushButton('Reload')
        btn.clicked.connect(self.loadMIDIData)
        btnLayout.addWidget(btn)

        ctlLayout.addWidget(QLabel(f'MIDI Input/Output:  {self.midi.getInputPortname()} / {self.midi.getOutputPortname()}'))

        showWidget = QWidget()
        showLayout = QHBoxLayout()
        showWidget.setLayout(showLayout)
        self.btnPedal = QCheckBox('Pedal Anzeigen')
        self.btnPedal.setChecked(True)
        self.btnPedal.clicked.connect(self.repaint)
        showLayout.addWidget(self.btnPedal)
        self.plotSelect = QComboBox()
        self.plotSelect.addItems(["nix", "Pedal", "Pegel", "Tempo", "Legato"])
        self.plotSelect.currentIndexChanged.connect( self.plotIndexChange )
        showLayout.addWidget(QLabel('Anzeige: '))
        showLayout.addWidget(self.plotSelect)
        ctlLayout.addWidget(showWidget)

        nt = self.setup.getInt('nTakte')
        widSpeed, self.speedSpinBox = self.spinArea('bpm', 5, 140, self.partiture.bpm, self.setSpeed)
        widFirst, self.firstSpinBox = self.spinArea(f'Erster Takt 1...{nt+1}', 1, nt+1, self.setup.getInt('ersterTakt'), self.setFirst)



        spinner = QWidget()
        spLayout = QHBoxLayout()
        spinner.setLayout(spLayout)
        spLayout.addWidget(widSpeed)
        spLayout.addWidget(widFirst)
        ctlLayout.addWidget(spinner)

        topLayout.addWidget(buttonWidget)

        return me
    def abspielen(self):
        list = []
        tScale = 60/self.setup.getFloat('bpm')/64
        for tone in self.soll:
            ton  = tone.position * tScale
            toff = (tone.position + tone.ticks) * tScale
            list.append(MidiCMD(ton, 0, tone.taste, 50, True))
            list.append(MidiCMD(toff, 0, tone.taste, 0, False))
        self.midi.playList(list)

    def wiederholen(self):
        if len(self.gespielt) < 1: return
        list = []
        tScale = 60/self.setup.getFloat('bpm')/64
        for tone in self.gespielt:
            ton  = tone.position * tScale
            toff = (tone.position + tone.ticks) * tScale
            list.append(MidiCMD(ton, 0, tone.taste, tone.level, True))
            list.append(MidiCMD(toff, 0, tone.taste, 0, False))
        self.midi.playList(list)
    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            if self.timeWindow > 128:
                self.timeStart += self.timeWindow * 0.1
                self.timeWindow *= 0.8
        else:
            self.timeStart = max(0, self.timeStart - self.timeWindow * 0.1)
            self.timeWindow *= 1.2
        self.repaint()
    def mousePressEvent(self, event) -> None:
        event.accept()
        self.lastPos = event.localPos().x()
    def mouseMoveEvent(self, event) -> None:
        event.accept()
        if self.lastPos < 0: return
        newPos = event.localPos().x()
        xMove = -(newPos - self.lastPos) / self.windowWidth
        self.timeStart = max(0, self.timeStart + xMove * self.timeWindow)
        self.lastPos = newPos
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

    def buildSoll(self, w, hTotal):
        usePedal = self.btnPedal.checkState() and (len(self.pedal.measuredTimes) > 0)
        fm = self.fontMetrics()
        xExtra = 80
        xStart = xExtra + 20
        xEnd = w - 20
        tScale = (xEnd - xStart) / self.timeWindow
        mapTime2X = np.polyfit(np.array([self.timeStart, self.timeStart + self.timeWindow]), np.array([xStart, xEnd]), 1)

        self.soll = list(self.setup.partiture.voices)
        self.violineMin, self.violineMax, self.bassMin, self.bassMax = 2, 10, -10, -2
        for t in self.soll + self.gespielt:
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
        dZwischen = 20

        hPlot =  dZwischen + int(hTotal / 5) if self.plotIndex > 0 else 0
        if self.plotIndex == 1: hPlot = int(hPlot / 2)
        d = int(float(hTotal - dOben - dUnten - dZwischen - hPlot) / float(nv + nb))
        d2 = int(d / 2)
        dSpace = 2
        dl = d - dSpace
        y0Violine = dOben + self.violineMax * d + d2
        y0Bass    = dOben + dZwischen + (self.bassMax + nv) * d + d2
        y0Plot    = dOben + 3 * dZwischen + (nb + nv) * d
        hPlot -= dZwischen

        self.p.setBrush(QBrush(QColor(255,255,255)))
        self.p.drawRect(xStart-2-xExtra, dOben- 1, xEnd - xStart + 4 + xExtra, d * nv)
        self.p.drawRect(xStart-2-xExtra, dOben + nv * d + dZwischen- 1, xEnd - xStart + 4 + xExtra, d * nb)

        if self.plotIndex > 0:
            self.p.drawRect(xStart - 2, y0Plot, xEnd - xStart + 4, hPlot)
            text = self.plotSelect.currentText()
            self.p.drawText(int(0.5 * (xStart + xEnd - fm.width(text))), y0Plot - dZwischen + 5, text)

        if usePedal:
            xListPedal, wListPedal = self.pedal.getPlotRegions(xStart, xEnd, self.timeStart, tScale)
            for i in range(len(xListPedal)):
                self.p.fillRect(xListPedal[i], dOben, wListPedal[i], d * nv - 2, QColor(245,245,245))
                self.p.fillRect(xListPedal[i], dOben + nv * d + dZwischen, wListPedal[i], d * nb - 2, QColor(245,245,245))
                if self.plotIndex > 0: self.p.fillRect(xListPedal[i], y0Plot, wListPedal[i], hPlot, QColor(245, 245, 245))

        self.p.drawPixmap(xStart+2-xExtra, y0Violine - int(5.5*d), int(1.5*d), 3*d, self.violinePixmap)
        self.p.drawPixmap(xStart+2-xExtra, y0Bass    + int(3.4*d), int(1.4*d), int(1.8*d), self.bassPixmap)

        pen = QPen(QColor(0, 0, 0))
        pen.setWidth(3)
        self.p.setPen(pen)

        for notes in [self.soll, self.gespielt]:
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
        modes = [[self.soll, 1, 0, False], [self.gespielt, 0.5, 2, True], [self.gespielt, 0.7, 1, False]]
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
            if self.speedData['valid']:
                map = np.polyfit(np.array([0, max(1.2, self.speedData['max'])]), np.array([y0Plot + hPlot, y0Plot]), 1)
                speed = self.speedData['data']
                speedY = np.polyval(map, speed).astype(int)
                timesX = np.polyval(mapTime2X, self.speedData['times']).astype(int)

                mean = self.speedData['mean']
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
            for note in self.gespielt:
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
            for t in self.gespielt:
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
            x = np.polyval(mapTime2X, self.pedal.mappedTimes).astype(int)
            y = np.polyval(mapLevel2Y, self.pedal.level).astype(int)
            for i in range(len(x)-1):
                if x[i] > xEnd or x[i+1] < xStart: continue
                self.p.drawLine(x[i], y[i], x[i+1], y[i])
                self.p.drawLine(x[i+1], y[i], x[i+1], y[i+1])

        elif self.plotIndex > 0:
            for t in self.gespielt:
                t0 = t.mappedTime - self.timeStart
                if t0 < 0: continue
                t1 = t0 + t.ticks + t.pedalExtension
                if t0 >= self.timeWindow or (t1 < 0): continue
                t1 = min(t1, self.timeWindow)
                x0 = xStart + int(t0 * tScale)
                x1 = xStart + int(t1 * tScale)
                self.drawTone(self.p, t.level, x0, x1, y0Plot + hPlot, hPlot,50*tScale, self.plotIndex==1, colorMap[1][t.getColor()])


    def paintEvent(self, event):

        widget = self.notenWidget
        self.p = QPainter(widget)
        self.p.begin(self)

        self.p.setRenderHint(QPainter.Antialiasing)
        w = widget.width()
        h = widget.height()
        self.windowWidth = w
        self.p.setBrush(QBrush(QColor(230,230,230)))
        self.p.drawRect(0, 0, w, h)
        self.buildSoll(w, h)
        self.p.end()

    def getCandidates(self, listSoll, listIst, takt, tmin, tmax):
        # erzeuge listen von candiates
        candidatesSoll, candidatesIst = [], []
        startNext = self.partiture.taktStart[takt+1]
        # Alle soll Kondidaten in Takt <takt> und die ersten Noten im nächstem Takt
        for note in listSoll:
            if (note.takt - 1) < takt: continue
            candidatesSoll.append(note)
            if ((note.takt - 1) > takt) and (note.position > startNext): break
        # Alle ist Kandidaten im Zeitbereich
        for note in listIst:
            if not note.match is None: continue
            if note.position < tmin: continue
            if note.position > tmax: break
            candidatesIst.append(note)
        return candidatesSoll, candidatesIst

    def matchCandidates(self, list1, list2, mapping, tolerance, lock, ist2soll, soll2ist):
        t1,t2  = [], []
        # estimate the time mapping
        for note in list2:
            note.mappedTime = np.polyval(mapping, note.position)

        candidateList = list(list2)
        for note1 in list1:
            for candidate in candidateList:
                if (note1.taste != candidate.taste or
                    candidate.match is not None or
                    abs(note1.position - candidate.mappedTime)  > tolerance) : continue
                if lock: candidate.setMatch(note1)
                t1.append(note1.position)
                t2.append(candidate.position)
                candidateList.remove(candidate)
                break

        if len(t1) > 1:
            ist2soll = np.polyfit(t2, t1, 1)
            soll2ist = np.polyfit(t1, t2, 1)
        return ist2soll, soll2ist, len(list1) - len(t1)

    def legato(self):
        legatoTimes, legatoValues = [], []
        for s2 in range(1, len(self.soll)):
            soll2 = self.soll[s2]
            if soll2.match is None: continue
            for s1 in range(s2):
                soll1 = self.soll[s1]
                if soll1.match is None: continue
                if soll1.position + soll1.ticks != soll2.position: continue
                ist1 = soll1.match

                ist2 = soll2.match
                legato = (ist1.position + ist1.ticks - ist2.position) * self.ticks2sec * 1000
                ist2.legato = legato
                if ist1.pedalExtension == 0:
                    legatoTimes.append(ist2.mappedTime)
                    legatoValues.append(legato)

        self.legatoData = self.analyseData(legatoTimes, legatoValues)
        self.legatoTacho.setRanges(self.legatoData['ranges'])
        self.legatoTacho.setValue(self.legatoData['mean'])


    def rubatoMeter(self):
        times, diff = [], []
        for note in self.soll:
            if note.match is not None:
                diff.append(note.position - note.match.mappedTime)
                times.append(note.position)

        self.rubatoData = self.analyseData(times, np.abs(np.array(diff)))
        self.rubatoTacho.setRanges(self.rubatoData['ranges'])
        self.rubatoTacho.setValue(self.rubatoData['mean'])


    def speedoMeter(self):
        n = len(self.partiture.taktStart)
        iMax = len(self.soll) - 1
        timePoints = 32 * np.linspace(0, n * 8, n * 8)
        iFirst, iLast = 0,0
        validSpeeds = []
        validTimes  = []
        for iTime,t in enumerate(timePoints):
            while iFirst < iMax and self.soll[iFirst].position < t - 128:
                iFirst += 1
            while iLast  < iMax and self.soll[iLast].position < t + 128:
                iLast += 1
            t1, t2 = [], []
            for i in range(iFirst, iLast + 1):
                if self.soll[i].match is not None:
                    t1.append(self.soll[i].position)
                    t2.append(self.soll[i].match.position)
            if len(t1) > 3:
                poly = np.polyfit(t2, t1, 1)
                validSpeeds.append(poly[0])
                validTimes.append(t)
        self.speedData = self.analyseData(validTimes, validSpeeds)
        if self.speedData['valid']:
            self.tempoTacho.setRanges(self.speedData['ranges'] * self.partiture.bpm)
            self.tempoTacho.setValue(self.speedData['mean'] * self.partiture.bpm)
        else:
            self.tempoTacho.setRanges([])
            self.tempoTacho.setValue(None)

    def analyseData(self, times, data):
        st = {'valid': False, 'mean': None, 'ranges': []}
        if times is None or len(times) < 1: return st
        st['valid'] = True
        data = np.array(data)
        st['data'] =  data
        st['times'] = np.array(times)
        vmin  = st['min'] = np.min(data)
        vmean = st['mean'] = np.mean(data)
        vmax  = st['max'] = np.max(data)
        vstd  = st['std'] = np.sqrt(np.var(data))
        st['ranges'] = np.array([[vmin, vmax], [max(vmin, vmean - vstd), min(vmax, vmean + vstd)]])
        return st

    def superMatcher(self):
        takt1 = self.setup.getInt('ersterTakt') - 1
        for note in self.soll: note.match = None
        offset = self.partiture.taktStart[takt1]
        for note in self.gespielt:
            note.match = None
            note.position += offset
        self.pedal.adjustMeasuredTimes(offset)

        cSoll, cIst = self.getCandidates(self.soll, self.gespielt, takt1, self.partiture.taktStart[takt1]-1, self.partiture.taktStart[takt1+1] * 1.5)
        ist2soll, soll2ist, rem = self.matchCandidates(cSoll, cIst, np.polyfit([0, 1], [0, 1], 1),  128, False, [0,1], [0,1])
        ist2soll, soll2ist, rem = self.matchCandidates(cSoll, cIst, ist2soll, 64, False, ist2soll, soll2ist)
        t0, t1 = self.partiture.taktStart[takt1], self.partiture.taktStart[takt1+1]
        self.tMapSoll = [t0]
        self.tMapIst  = [t0]
        for takt in range(takt1,len(self.partiture.taktStart) -1):
            t0, t1 = self.partiture.taktStart[takt], self.partiture.taktStart[takt+1]
            dQuarter = 32 * ist2soll[0]
            tmin = np.polyval(soll2ist, (t0 - dQuarter))
            tmax = np.polyval(soll2ist, (t1 + 2 * dQuarter))
            cSoll, cIst = self.getCandidates(self.soll, self.gespielt, takt, tmin, tmax)
            if len(cIst) < 1:
                self.tMapIst.append(self.tMapIst[-1] + (t1 - t0))
                self.tMapSoll.append(t1)
            else:
                ist2soll, soll2ist,rem = self.matchCandidates(cSoll, cIst, ist2soll, 64, True, ist2soll, soll2ist)
                self.tMapIst[-1] = 0.5 * (self.tMapIst[-1] + np.polyval(soll2ist, t0))
                self.tMapSoll.append(t1)
                self.tMapIst.append(np.polyval(soll2ist, t1))
        for i in range(len(self.pedal.measuredTimes)):
            self.pedal.mappedTimes[i] = np.interp(self.pedal.measuredTimes[i], self.tMapIst, self.tMapSoll)
        for note in self.gespielt:
            note.mappedTime = np.interp(note.position, self.tMapIst, self.tMapSoll)
            note.checkPedal(self.pedal)
        self.speedoMeter()
        self.rubatoMeter()
        self.legato()

class Tacho(QWidget):
    def __init__(self, title, vMin, vMax, vRes, form, parent = None):
        QWidget.__init__(self, parent)
        self.title = title
        self.vMin = vMin
        self.vMax = vMax
        self.vRes = vRes
        self.arc = 170
        self.arc2 = self.arc / 2
        self.form = form
        self.value = None
        self.subTicks = 4
        self.ranges = None
        self.tickColor = Qt.white
        self.genTicks()

    def setRanges(self, ranges):
        self.ranges = ranges
    def setValue(self, value):
        self.value = value
    def value2angle(self, value):
        value = min(max(self.vMin, value), self.vMax)
        return ((value - self.vMin) / (self.vMax - self.vMin) - 0.5 )* self.arc

    def value2point(self, value, radius):
        angle = self.value2angle(value) * np.pi / 180
        cosA = np.cos(angle)
        sinA = np.sin(angle)
        return int(self.cx + radius * sinA), int(self.cy - radius * cosA)

    def drawRadial(self, value, r0, r1, width, color):
        x0, y0 = self.value2point(value, r0)
        x1, y1 = self.value2point(value, r1)
        self.p.setPen(QPen(color, width))
        self.p.drawLine(x0, y0, x1, y1)

    def drawRadialOld(self, angle, r0, r1, width, color):
        angle *= np.pi / 180.0
        cosA = np.cos(angle)
        sinA = np.sin(angle)
        x0 = int(self.cx + r0 * sinA)
        x1 = int(self.cx + r1 * sinA)
        y0 = int(self.cy - r0 * cosA)
        y1 = int(self.cy - r1 * cosA)
        self.p.setPen(QPen(color, width))
        self.p.drawLine(x0, y0, x1, y1)

    def genTicks(self):
        v0 = np.floor(self.vMin / self.vRes) * self.vRes
        if v0 < self.vMin: v0 += self.vRes
        self.tickValue = []
        self.tickText  = []
        while (v0) <= self.vMax:
            self.tickValue.append(v0)
            self.tickText.append(self.form.format(value = v0))
            v0 += self.vRes

    def drawRanges(self):
        r = self.rRing * 0.9
        width = 16
        self.p.setPen(QPen(Qt.red, width))
        for range in self.ranges:
            a0 = self.value2angle(range[0])
            a1 = self.value2angle(range[1])
            self.p.drawArc(int(self.cx - r), int(self.cy - r), int(2 * r), int(2 * r),int((90 - a0) * 16), int((a0-a1) * 16))
            width -= 6
            self.p.setPen(QPen(Qt.green, width))

    def drawTicks(self):
        dSub = self.vRes / (self.subTicks+1)
        for i in range(len(self.tickText)):
            value = self.tickValue[i]
            self.drawRadial(value, self.rRing, self.rRing * 1.1, 2, self.tickColor)
            for j in range(1, self.subTicks+1):
                self.drawRadial(value + j * dSub, self.rRing, self.rRing * 1.05, 2, self.tickColor)
            x,y = self.value2point(value, self.rText)
            x -= int(self.fm.width(self.tickText[i]) / 2)
            self.p.drawText(x, y + self.cch2, self.tickText[i])

    def paintEvent(self, event):
        self.p = QPainter(self)
        self.p.setRenderHint(QPainter.Antialiasing)
        self.p.begin(self)
        self.fm = self.fontMetrics()
        self.cch = self.fm.height()
        self.cch2 = int(self.cch / 2)
        w = self.width()
        h = self.height()

        self.p.fillRect(2, 0, w-4, h, QColor(0, 0, 0))
        self.p.setPen(QPen(Qt.white))
        self.p.drawText(int(w/2 - self.fm.width(self.title)/2), int(self.cch * 1.5), self.title)

        self.cx = int(w/2)
        self.cy = h - 10

        self.rText = h - 20 - 2 * self.cch
        self.rRing = self.rText - 2 * self.cch
        self.p.drawArc(int(w/2 - self.rRing), int(self.cy - self.rRing), int(2 * self.rRing), int(2 * self.rRing), int((180 - self.arc) * 8), int(self.arc*16))

        self.drawTicks()
        if self.ranges is not None: self.drawRanges()
        if not self.value is None:
            self.drawRadial(self.value, 0, self.rRing * 0.9, 3, Qt.white)
            self.drawRadial(self.value, 0, self.rRing * 0.7, 10, Qt.green)

        r=30
        self.p.setPen(QPen(Qt.white, 1))
        self.p.setBrush(QBrush(Qt.darkGray, Qt.SolidPattern))
        self.p.drawEllipse(self.cx - r, self.cy - r , 2*r, 2*r)

        self.p.end()

class Pedal():
    threshold = 0
    def __init__(self):
        self.measuredTimes = []
        self.mappedTimes = []
        self.level = []

    def add(self, time, level):
        self.measuredTimes.append(time)
        self.mappedTimes.append(time)
        self.level.append(level)

    def adjustMeasuredTimes(self, adjust):
        for i in range(len(self.measuredTimes)):
            self.measuredTimes[i] += adjust

    def isOnUntil(self, time):
        n = len(self.measuredTimes)
        if n < 1: return False, 0.0
        iBefore = 0
        for i in range(n):
            if self.mappedTimes[i] < time: iBefore = i
        if self.level[iBefore] < Pedal.threshold: return False, 0.0
        iOff = self.indexPedal(iBefore,False)
        return True, self.mappedTimes[iOff]

    def indexPedal(self, start, on):
        if on:
            for i in range(start, len(self.mappedTimes)):
                if self.level[i] > Pedal.threshold: return i
        else:
            for i in range(start, len(self.mappedTimes)):
                if self.level[i] <= Pedal.threshold: return i
            return len(self.mappedTimes) - 1
        return -1

    def getPlotRegions(self, x0, xend, t0, tScale):
        n = len(self.mappedTimes)
        xList, wList = [], []
        if n < 1: return xList, wList
        index = 0
        while index < n:
            indexOn = self.indexPedal(index, True)
            if indexOn < 0: break
            xon =  x0 + int((self.mappedTimes[indexOn]  - t0) * tScale)
            if xon >= xend: break

            indexOff = self.indexPedal(indexOn, False)
            if indexOn == indexOff: break
            index = indexOff + 1
            xoff = x0 + int((self.mappedTimes[indexOff] - t0) * tScale)
            if xoff < x0: continue
            xon = max(xon, x0)
            xList.append(xon)
            wList.append(min(xoff, xend) - xon)

        return xList, wList
