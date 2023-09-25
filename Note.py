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
        self.id = 0

    def setID(self, id):
        self.id = id
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