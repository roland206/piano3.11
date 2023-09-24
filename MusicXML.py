import xml.etree.ElementTree as ET
from Note import Note
def getDuration(item):
    item = item.find('duration')
    return int(item.text)
class MusicXML():
    def __init__(self, filename):

        self.bpm = 80
        self.voices = []
        self.taktStart = []
        self.nTakte = 0
        try:
            tree = ET.parse(filename)
            root = tree.getroot()
        except:
            self.taktStart = [0]
            return
        name2pitch = {'C':0, 'D':2, 'E':4, 'F':5, 'G':7, 'A':9, 'H':11, 'B': 11 }
        pos = 0
        level = 90
        item = root.find('part').find('measure').find('attributes').find('divisions')
        scale = 64 /int(item.text)
        for mes in root.iter('measure'):
            takt = int(mes.attrib['number'])
            self.taktStart.append(pos*scale)
            for measureItem in mes.iter('*'):
                if   measureItem.tag == 'backup':  pos -= getDuration(measureItem)
                elif measureItem.tag == 'forward': pos += getDuration(measureItem)
                elif measureItem.tag == 'direction':
                    sound = measureItem.find('sound')
                    if sound is not None:
                        if 'dynamics' in sound.attrib: level = int(float(sound.attrib['dynamics']))
#                       if 'tempo' in sound.attrib: self.bpm = int(float(sound.attrib['tempo']))
                elif measureItem.tag == 'note':
                    pause = False
                    chord = False
                    tie = ''
                    staff = 1
                    duration = 0
                    for item in measureItem.findall('*'):
                        if    item.tag == 'staff': staff = int(item.text)
                        elif item.tag == 'tie': tie = item.attrib['type']
                        elif item.tag == 'chord': pos -= lastStep
                        elif item.tag == 'rest':  pause = True
                        elif item.tag == 'duration': duration = int(item.text)
                        elif item.tag == 'voice': voice = int(item.text)
                        elif item.tag == 'pitch':
                            taste = 12
                            for p in item.findall('*'):
                                if p.tag == 'step':   taste += name2pitch[p.text]
                                if p.tag == 'alter':  taste += int(p.text)
                                if p.tag == 'octave': taste += 12 * int(p.text)

                    if not pause:
                        if tie == 'stop':
                            for i in range(len(self.voices) - 1, -1, -1):
                                if self.voices[i].taste == taste:
                                    self.voices[i].ticks += max(duration* scale, 8)
                                    break
                        else:
                            self.voices.append(Note(taste, max(duration* scale, 8), pos * scale, takt, staff==1, level = level))
                    lastStep = duration
                    pos += duration
        self.taktStart.append(pos * scale)
        self.voices = sorted(self.voices, key=lambda n: n.position)
        self.nTakte = len(self.taktStart) - 1
        return
