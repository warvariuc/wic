'''Author: Victor Varvariuc <victor.varvariuc@gmail.com'''

import os, sys
import math, random
from PyQt4 import QtCore, QtGui

from wic import w
from wic.forms import WForm, setValue, getValue


class Form(WForm):
    '''Lissajous figures in new fashion :).'''

    def on_open(self): 
        global dt
        dt = Liss(None)
        self.placeholder.addWidget(dt)
        dt.show()
        dt.antialiasing = True
        self.antialiasing.setChecked(True)
    
    @QtCore.pyqtSlot()
    def on_buttonStart_clicked(self): 
        if dt.timer.isActive():
            dt.stop()
            self.buttonStart.setText('Start')
        else:
            dt.start()
            self.buttonStart.setText('Stop')
    
    @QtCore.pyqtSlot()
    def on_buttonReset_clicked(self): 
        dt.resetParams()
    
    def on_antialiasing_stateChanged(self, state): 
        dt.antialiasing = state



class Liss(QtGui.QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.NextStep)

        self.resetParams()

        self.painter = QtGui.QPainter()
        self.antialiasing = True

        self.pen1 = QtGui.QPen(QtGui.QColor('yellow'), 2, QtCore.Qt.SolidLine)
        self.pen2 = QtGui.QPen(QtGui.QColor('white'), 2, QtCore.Qt.SolidLine)
        
        self.NextStep()


    def start(self):
        self.timer.start(40)

    def stop(self):
        self.timer.stop()

    def resetParams(self): # default values
        self.M = random.randint(10, 10000)
        self.L = random.randint(10, 10000)
        self.N = random.randint(5, 40) # number of line strokes
        self.B = 2 * math.pi / self.N # intermediar coeficient
        self.step = 0 # current step
        self.SPT = 100 # spt - steps per transition from one figure to another
        self.d = 0 # current delta which depends on frame, intermediar coeficient representing current step
        self.pause = 0 # number of steps to wait when a transition is over
        self.stepDirection = 1

    def NextStep(self): # increase step and calculate coeficients for it
        if self.pause > 0:
            self.pause -= 1
            return
        self.step += self.stepDirection
        if self.step > self.SPT or self.step < 0:
            self.step =(self.step + self.SPT) % self.SPT
            self.M += self.stepDirection
            self.L += self.stepDirection
            self.pause = 20
        self.d = 0.5 * (1 - math.cos(math.pi * self.step / self.SPT)) # angular step
        self.l = (self.L + self.d) * self.B
        self.m = (self.M + self.d) * self.B
        self.update()

    def paintEvent(self, event):
        if not self.pixmap: 
            return
        self.pixmap.fill(QtGui.QColor('black'))

        w2 = self.w // 2 #center
        h2 = self.h // 2
        x1 = w2
        y1 = h2 * 2
        
        self.painter.begin(self.pixmap)
        self.painter.setRenderHint(QtGui.QPainter.Antialiasing, self.antialiasing)
        for k in range(1, self.N + 1):
            x2 = round(w2 * (math.sin(k * self.m) + 1)) #round(n) = rounds half to even
            y2 = round(h2 * (math.cos(k * self.l) + 1))
            self.painter.setPen(self.pen1 if k % 2 else self.pen2)
            self.painter.drawLine(x1, y1, x2, y2)
            x1, y1 = x2, y2

        self.painter.end()

        self.painter.begin(self)
        self.painter.drawPixmap(0, 0, self.pixmap)
        self.painter.end()

    def resizeEvent(self, event):
        self.w = self.width()
        self.h = self.height()
        self.pixmap = QtGui.QPixmap(self.w, self.h)
    