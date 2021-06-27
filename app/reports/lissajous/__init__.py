__author__ = 'Victor Varvariuc <victor.varvariuc@gmail.com>'

import math, random

from PyQt5 import QtCore, QtGui, QtWidgets

import wic.forms


class Form(wic.forms.Form):
    """
    Lissajous figures in new fashion.
    """
    def on_open(self):
        self.dt = Liss(None)
        self.placeholder.addWidget(self.dt)
        self.dt.show()
        self.dt.antialiasing = True
        self._.antialiasing = True
    
    @QtCore.pyqtSlot()
    def on_buttonStart_clicked(self): 
        if self.dt.timer.isActive():
            self.dt.stop()
            self.buttonStart.setText('Start')
        else:
            self.dt.start()
            self.buttonStart.setText('Stop')
    
    @QtCore.pyqtSlot()
    def on_buttonReset_clicked(self): 
        self.dt.resetParams()
    
    def on_antialiasing_stateChanged(self, state): 
        self.dt.antialiasing = state


class Liss(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.next_step)

        self.resetParams()

        self.painter = QtGui.QPainter()
        self.antialiasing = True

        self.pen1 = QtGui.QPen(QtGui.QColor('yellow'), 2, QtCore.Qt.SolidLine)
        self.pen2 = QtGui.QPen(QtGui.QColor('white'), 2, QtCore.Qt.SolidLine)
        
        self.next_step()

    def start(self):
        self.timer.start(40)

    def stop(self):
        self.timer.stop()

    def resetParams(self):
        # Set default values
        self.M = random.randint(10, 10000)
        self.L = random.randint(10, 10000)
        self.N = random.randint(5, 40)  # number of line strokes
        self.B = 2 * math.pi / self.N  # intermediar coeficient
        self.step = 0  # current step
        # Steps per transition from one figure to another
        self.steps_per_transition = 100
        # current delta which depends on frame, intermediary coefficient representing current step
        self.d = 0
        self.pause = 0  # number of steps to wait when a transition is over
        self.step_direction = 1

    def next_step(self):
        # increase step and calculate coefficients for it
        if self.pause > 0:
            self.pause -= 1
            return
        self.step += self.step_direction
        if self.step > self.steps_per_transition or self.step < 0:
            self.step = (self.step + self.steps_per_transition) % self.steps_per_transition
            self.M += self.step_direction
            self.L += self.step_direction
            self.pause = 20
        self.d = 0.5 * (1 - math.cos(math.pi * self.step / self.steps_per_transition)) # angular step
        self.l = (self.L + self.d) * self.B
        self.m = (self.M + self.d) * self.B
        self.update()

    def paintEvent(self, event):
        if not self.pixmap: 
            return
        self.pixmap.fill(QtGui.QColor('black'))

        w2 = self.w // 2  # center
        h2 = self.h // 2
        x1 = w2
        y1 = h2 * 2
        
        self.painter.begin(self.pixmap)
        self.painter.setRenderHint(QtGui.QPainter.Antialiasing, self.antialiasing)
        for k in range(1, self.N + 1):
            x2 = round(w2 * (math.sin(k * self.m) + 1))  # round(n) = rounds half to even
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
