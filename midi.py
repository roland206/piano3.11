import time
import threading
from threading import Semaphore
import rtmidi2

class MidiCMD():
    def __init__(self, time, channel, key, level, on):
        self.time = time
        self.channel = channel
        self.key = key
        self.level = level
        self.on = on


def callback(message, timeStamp):
    if False:
        print(message, timeStamp)
    global lastCall, midiObject, timeBuffer, cmdBuffer, stopKey, stopPedal
    if len(timeBuffer) == 0:
        lastCall = 0
    else:
        lastCall += timeStamp

    if stopKey:
        if (message[0] == 128) and message[1] == 21: stopKey = False
        return

    if stopPedal:
        if (message[0] == 176) and message[1] == 67: stopPedal = message[2] > 0
        return

    stopKey =   (message[0] == 144) and (message[1] == 21)
    stopPedal = (message[0] == 176) and (message[1] == 67) and message[2] > 0
    if stopKey or stopPedal:
        if len(timeBuffer) > 0:
            midiObject.bufferFull(cmdBuffer, timeBuffer)
        cmdBuffer, timeBuffer = [], []
        lastCall = 0
    else:
        cmdBuffer.append(message)
        timeBuffer.append(lastCall)

class Midi():
    def __init__(self, port, caller):

        global midiObject, timeBuffer, cmdBuffer, stopKey, stopPedal
        global token, playList, running, stop

        midiObject = caller
        timeBuffer, cmdBuffer = [], []
        stopKey = stopPedal = False

        self.inputPortname = 'nicht verfügbar'
        self.outputPortname = 'nicht verfügbar'

        inPorts  = self.getInputPorts()
        outPorts = self.getOutputPorts()

        self.midi_out = rtmidi2.MidiOut()
        port = min(port, len(outPorts) - 1)
        self.midi_out.open_port(port)
        self.outputPortname = outPorts[port]

        if (len(inPorts) > 0):
            self.midi_in = rtmidi2.MidiIn()
            self.midi_in.callback = callback
            port = min(port, len(inPorts) - 1)
            self.midi_in.open_port(port)
            self.inputPortname = inPorts[port]

        token = Semaphore()
        token.acquire()
        running = False
        stop = False
        thread = threading.Thread(target=self.outputer)
        thread.start()

    def getInputPortname(self):  return self.inputPortname
    def getOutputPortname(self): return self.outputPortname
    def getInputPorts(self):     return rtmidi2.get_in_ports()
    def getOutputPorts(self):    return rtmidi2.get_out_ports()

    def sortList(self, list):
        newList = sorted(list, key=lambda n: n.time)
        return newList

    def outputer(self):
        global token, playList, running, stop

        while(True):
            token.acquire()
            running = True
            list = self.sortList(playList)
            token.release()
            now = list[0].time
            for cmd in list:
                if stop: break
                if cmd.time > now:
                    time.sleep(cmd.time - now)
                    now = cmd.time
                if cmd.on:
                    self.midi_out.send_noteon(cmd.channel, cmd.key, cmd.level)
                else:
                    self.midi_out.send_noteoff(cmd.channel, cmd.key)
            running = False

    def playList(self, list):
        global token, playList, running, stop
        if running :
            stop = True
            return
        playList = list
        stop = False
        token.release()
        while(not running):
            time.sleep(1)
        token.acquire()


