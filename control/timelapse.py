# -*- coding: utf-8 -*-
"""
Created on Wed Nov 6 11:45:51 2019

Widget for doing timelapse imaging in Imspector, controlled from Tempesta.

@author: jonatanalvelid
"""

from pyqtgraph.Qt import QtGui
import time
import threading


# communication with Imspector.
class TimelapseWidget(QtGui.QFrame):

    def __init__(self, imspector, main=None, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.setMinimumSize(200, 100)  # Set the minimum size of the widget

        self.imspector = imspector
        self.main = main
        self.timelapseActiveVar = False  # bool telling if timelapse is active
        self.framenumber = 0  # number of current frame (0-(num of frames-1))
        self.frametime = 0  # frametime
        self.countrows = 0  # number of rows scanned in Imspector meas
        self.rowsperframe = 0  # number of rows per frame in Imspector meas
        self.numberofframes = 0  # number of frames for timelapse

        self.framesLabel = QtGui.QLabel('Number of frames')
        self.framesEdit = QtGui.QLineEdit('1')
        self.frametimeLabel = QtGui.QLabel('Time between frames [s]')
        self.frametimeEdit = QtGui.QLineEdit('60')
        self.initTimelapseButton = QtGui.QPushButton('Initialize timelapse')
        self.initTimelapseButton.clicked.connect(self.inittimelapse)

        # Add status bar, a non-editable text, that tells the current state
        self.statusLabel = QtGui.QLabel('Status:')
        self.statusText = QtGui.QLineEdit(
                'Click "Initialize timelapse" to start timelapse acquisition')
        self.statusText.setReadOnly(True)

        # GUI layout
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.framesLabel, 0, 0)
        grid.addWidget(self.frametimeLabel, 0, 1)

        grid.addWidget(self.framesEdit, 1, 0)
        grid.addWidget(self.frametimeEdit, 1, 1)

        grid.addWidget(self.initTimelapseButton, 2, 0)

        grid.addWidget(self.statusLabel, 3, 0, 1, 1)
        grid.addWidget(self.statusText, 3, 1, 1, 4)

    def __call__(self):
        self.countrows = self.countrows + 1
        if self.countrows == self.rowsperframe:
            # Check if last step has been taken
            if self.framenumber == self.numberofframes:
                # Finish timelapse
                self.reptimer.stop()
                self.endtimelapse()
            else:
                # Pause measurement in Imspector
                self.imspector.pause(self.immeasurement)
                self.countrows = 0
                self.statusText.setText('Timelapse in progress, recorded frames: %d of %d' %
                                        (self.framenumber,
                                         self.numberofframes))

    def inittimelapse(self):
        if not self.timelapseActiveVar:
            self.timelapseActiveVar = True
            self.initTimelapseButton.setText('Reset/stop timelapse')
            # Get the frametime in s
            self.frametime = float(self.frametimeEdit.text())
            self.numberofframes = int(self.framesEdit.text())
            self.framenumber = 0
            self.immeasurement = self.imspector.active_measurement()
            self.measurementparams = self.immeasurement.parameters('')
            # Double check if measurement in imspector is stack with the third
            # axis as the Sync 0 axis. Also check if number of frames in Sync 0
            # is at least as many as the number of frames here. Also connect
            # end of frame-signal to __call__ function.
            if self.measurementparams['Sync']['0Res'] == self.numberofframes:
                if self.measurementparams['Measurement']['ThdAxis'] == 'Sync 0':
                    self.statusText.setText('One-color timelapse started, recodring frame: %d of %d' % (self.framenumber+1, self.numberofframes))
                    self.imspector.connect_end(self,1)
                    self.rowsperframe = self.measurementparams['NiDAQ6353'][':YRes']
                elif self.measurementparams['Measurement']['SecAxis'] == 'NiDAQ6353 DACs::4' and self.measurementparams['Measurement']['FthAxis'] == 'Sync 0':
                    self.statusText.setText('Two-color timelapse started, recording frame: %d of %d' % (self.framenumber+1, self.numberofframes))
                    self.imspector.connect_end(self,1)
                    # Use double the number of rows, for two-color imaging
                    self.rowsperframe = 2*self.measurementparams['NiDAQ6353'][':YRes']
                else:
                    self.statusText.setText('Axises in Imspector are not properly set-up for a tiling. Double check your settings.')
                    self.endtimelapse()
                    return
                self.reptimer = RepeatedTimer(self.frametime, self.nextframe)
                self.nextframe()
            else:
                self.statusText.setText('Number of frames in Imspector and here do not agree. Double check your settings.')
                self.endtimelapse()
                return

        else:
            self.reptimer.stop()
            self.endtimelapse()

    def nextframe(self):
        if self.timelapseActiveVar:
            # Change frame number to next frame, resume Imsp measurement
            self.imspector.pause(self.immeasurement)
            self.statusText.setText('Timelapse in progress, recording frame: %d of %d' %
                                        (self.framenumber+1,
                                         self.numberofframes))
            self.framenumber = self.framenumber + 1

    def endtimelapse(self):
        # Do all the things needed to be done when you finish or end a tiling
        self.imspector.disconnect_end(self, 1)
        self.timelapseActiveVar = False
        self.framenumber = 0
        self.countrows = 0
        self.initTimelapseButton.setText('Initialize timelapse')
        self.statusText.setText('Click "Initialize timelapse" to start timelapse acquisition')

    def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)


if __name__ == '__main__':

    app = QtGui.QApplication([])

    win = TimelapseWidget()
    win.show()
    app.exec_()


# From: https://stackoverflow.com/questions/474528/what-is-the-best-way-to-repeatedly-execute-a-function-every-x-seconds-in-python  /eraoul answer
# Timer class that can execute function every interval
class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.next_call = time.time()
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self.next_call += self.interval
            self._timer = threading.Timer(self.next_call - time.time(),
                                          self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False
