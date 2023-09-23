import xml.etree.ElementTree as ET

class Voices():
    def __init__(self):
        self.insertAt = 0
        self.tuplet = False
        self.ticksNames = {
            "64th": 4, "32nd": 8, "16th": 16, "eighth": 32,
            "quarter": 64, "half": 128, "whole": 256, "measure": 256}
        self.toene = []
        self.taktStart = [0]
        self.appList = []

    def startTuplet(self, xmlSection):
        self.tuplet = True
        self.tupletNormal = int(xmlSection.find('normalNotes').text)
        self.tupletActual = int(xmlSection.find('actualNotes').text)

    def endTuplet(self):
        self.tuplet = False

    def setPos(self, pos, takt):
        self.insertAt = pos
        self.takt = takt
        if self.taktStart[-1] < pos: self.taktStart.append(pos)

    def getPos(self):
        return self.insertAt

    def addDuration(self, xmlTree, adjust):
        duration = xmlTree.find('durationType')
        ticks = self.ticksNames[duration.text]

        dots = xmlTree.find('dots')
        if dots != None:
            if dots.text == '1': ticks = ticks * 6 / 4
            if dots.text == '2': ticks = ticks * 7 / 4
        if self.tuplet: ticks *= self.tupletNormal / self.tupletActual
        if adjust: self.insertAt += ticks
        return ticks

    def addTaste(self, taste, ticks, spanner, violine, app):
        if spanner:
            for i in range(len(self.toene) - 1, -1, -1):
                if self.toene[i].taste == taste:
                    if self.toene[i].position + self.toene[i].ticks != self.insertAt:
                        print(f'Fehler letzer tone at {self.toene[i].position} länge {self.toene[i].ticks} ist position {self.insertAt}')
                    self.toene[i].ticks += ticks
                    return
            print('Sapnner nicht gefunden')


        if app:
            note = Note(taste, 4, self.insertAt - 4, self.takt, violine)
            for before in self.appList:
                before.position -= 4
            self.appList.append(note)
        else:
            note = Note(taste, ticks, self.insertAt, self.takt, violine)
            self.appList = []
        self.toene.append(note)

octTabLine  = [0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 5, 6]
octTabKreuz = [0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0]
class Note():
    def __init__(self, taste, ticks, position, takt, violine, level = 50):
        self.level = level
        self.taste = int(taste)
        self.ticks = ticks
        self.position = position
        self.mappedTime = position
        self.takt = takt
        self.violine = violine
        self.line = int(self.taste / 12) * 7 - 35 + octTabLine[self.taste % 12]
        self.kreuz = octTabKreuz[self.taste % 12]
        self.match = None
        self.pedalExtension = 0
        self.segment = 0
        self.legato = None

    def getColor(self):
        c = 0
        if not self.violine: c = 1
        if self.match is None: c += 2
        return c
    def setMatch(self, partner):
        self.match = partner
        self.violine = partner.violine
        partner.match = self

    def removeMatch(self):
        if self.match is None: return
        self.match.match = None
        self.match = None
    def checkPedal(self, pedal):
        isOn, tend =pedal.isOnUntil(self.mappedTime + self.ticks)
        if isOn:
            self.pedalExtension = tend - self.mappedTime - self.ticks
        else:
            self.pedalExtension = 0
    def getKeyList(self, liste, taste):
        index = []
        times  = []
        for i, n in enumerate(liste):
            if n.taste == taste:
                index.append(i)
                times.append(n.position)
        return index, times
class Partiture():
    def __init__(self, filename):

        tree = ET.parse(filename)
        root = tree.getroot()

        self.bpm = 80
        for bpm in root.iter('tempo'):
            self.bpm = round(60 * float(bpm.text))
            break

        time = Voices()
        for staff in root.iter('Staff'):
            violine = int(staff.attrib['id']) == 1
            takt = 0
            time.setPos(0, 1)
            for mes in staff.iter('Measure'):
                takt += 1
                taktStart = time.getPos()
                for voice in mes.iter('voice'):
                    time.setPos(taktStart,takt)
                    for item in voice.findall('*'):
                        if item.tag == 'Tuplet':    time.startTuplet(item)
                        if item.tag == 'endTuplet': time.endTuplet()
                        if item.tag == 'Rest':      time.addDuration(item, True)
                        if item.tag == 'Chord':
                            ticks = time.addDuration(item, False)
                            vorschlag = False
                            for x in item.findall('*'):
                                if x.tag == 'appoggiatura': vorschlag = True
                                if x.tag == 'Note':
                                    spanner = False
                                    for span in x.findall('Spanner'):
                                        if span.find('prev') != None: spanner = True
                                    time.addTaste(int(x.find('pitch').text), ticks, spanner, violine, vorschlag)
                            if not vorschlag: time.addDuration(item, True)
        self.voices = sorted(time.toene, key=lambda n: n.position)
        time.taktStart.append(time.insertAt)

        last = 0
        for n in time.toene:
            last = max(last, n.position + n.ticks)
        self.taktStart = []
        for start in time.taktStart:
            self.taktStart.append(start)
            if last < start: break
        self.nTakte = len(self.taktStart) - 1
        return

