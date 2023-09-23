import os.path
import glob
import xml.etree.cElementTree as ET

from partiture import Partiture

setupDefaults = {'bpm': 80, 'nLines' : 1, 'ersterTakt': 1, 'nTakte' : 1,
                 'partitureFile': 'spanner.mscx'}
class Setup():
    def __init__(self, filename = None):

        if filename is None:
            files = glob.glob("*.part")
            if len(files) == 0:
                filename = 'new.part'
                self.filename = filename
                self.root = ET.Element("data")
                for key in setupDefaults:
                    ET.SubElement(self.root, key).text = str(setupDefaults[key])
                self.save()
            else:
                filename = files[0]
                latestTime = os.path.getmtime(filename)
                for path in files:
                    updated = os.path.getmtime(path)
                    if updated > latestTime:
                        filename = path
                        latestTime = updated
        self.load(filename)

    def load(self, filename):
        self.filename = filename
        self.tree = ET.parse(filename)
        self.root = self.tree.getroot()
        self.partiture = None
        if len(self.getStr('partitureFile')) > 0:
            self.partiture = Partiture(self.getStr('partitureFile'))
            self.set('nTakte', min(self.getInt('nTakte'), self.partiture.nTakte))

    def save(self):
        tree = ET.ElementTree(self.root)
        ET.indent(tree, '  ')
        tree.write(self.filename, encoding="utf-8", xml_declaration=True)

    def set(self, token, value):
        slot = self.root.find(token)
        if slot is None:
            ET.SubElement(self.root, token).text = str(value)
        else:
            slot.text = str(value)
        self.save()

    def getTag(self, token):
        tag = self.root.find(token)
        if tag is None:
            print(f'Tag <{token}> not in setup')
        return tag

    def getStr(self, token):
        return self.getTag(token).text
    def getFloat(self, token):
        return float(self.getTag(token).text)
    def getInt(self, token):
        return int(self.getTag(token).text)
