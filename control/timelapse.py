# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 11:45:51 2019

Widget for doing timelapse imaging in Imspector, controlled from Tempesta.

@author: jonatan.alvelid
"""

import numpy as np
from pyqtgraph.Qt import QtGui
import time
import threading


# TODO: Fix this widget, for now copied from tiling.py, to perform timelapse
# communication with Imspector.
class TimelapseWidget(QtGui.QFrame):

    def __init__(self, imspector, main=None, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.setMinimumSize(2, 350)  # Set the minimum size of the widget

        self.imspector = imspector
        self.main = main
        self.timelapseActiveVar = False  # bool telling if timelapse is active
        self.framenumber = 0  # number of current frame (0-(num of frames-1))
        self.frametime = 0  # frametime
        self.countrows = 0  # number of rows scanned in Imspector meas
        self.rowsperframe = 0  # number of rows per frame in Imspector meas

        self.framesLabel = QtGui.QLabel('Number of frames, F')
        self.framesEdit = QtGui.QLineEdit('1')
        self.frametimeLabel = QtGui.QLabel('Time between frames [s]')
        self.frametimeEdit = QtGui.QLineEdit('60')
        self.initTimelapseButton = QtGui.QPushButton('Initialize timelapse')
        self.initTimelapseButton.clicked.connect(self.inittimelapse)

        # Add status bar, a non-editable text, that tells the current state
        self.statusLabel = QtGui.QLabel('Status:')
        self.statusText = QtGui.QLineEdit('Click "Initialize timelapse" to start timelapse acquisition')
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
            self.countrows = 0
            self.nextframe()
            self.statusText.setText('Tiling in progress, frame %d of %d' % (self.framenumber+1, self.numberofframes))
            # frame is finished

    def timelapseActiveVarChange(self):
        if self.timelapseActiveVar:
            self.timelapseActiveVar = False
        else:
            self.timelapseActiveVar = True

# TODO: This function has not changed at all.
    def inittimelapse(self):
        if not self.tilingActiveVar:
            self.tilingActiveVar = True
            self.initTilingButton.setText('Reset/stop tiling')
            # Get the tile step distance in um, i.e. tile size minus margin
            self.tilestepsize = float(self.tilesSizeEdit.text()) - float(self.tilesMarginEdit.text())
            self.numberofframes = int(self.tilesXEdit.text())*int(self.tilesYEdit.text())
            self.tilenumber = 0
            # Create a new tilefoci-array if this is a new focus check tiling
            if self.tilingFocusCheckVar:
                self.tilefoci = np.zeros(self.numberoftiles)
                self.statusText.setText('Setting tiling foci, tile %d of %d' % (self.tilenumber+1, self.numberoftiles))
            else:
                print(self.tilefoci)
            # If you want to do automatic tiling, check the number of rows in the active imspector measurement stack window
            # also connect the end of the frame-signal to the __call__ function
            if self.automaticTilingVar:
                self.immeasurement = self.imspector.active_measurement()
                self.measurementparams = self.immeasurement.parameters('')
                # Double check if the measurement in imspector is actually a stack with the thrid axis as the Sync 0 axis
                # Also check if the number of frames in Sync 0 is matchin the number of tiles!
                # Also check if the size of the tiles equals the size of the measurement in Imepsctor
                if self.measurementparams['Sync']['0Res'] == self.numberoftiles and self.measurementparams['NiDAQ6353'][':YLen'] == float(self.tilesSizeEdit.text()) and round(self.measurementparams['NiDAQ6353'][':XLen']) == float(self.tilesSizeEdit.text()):
                    if self.measurementparams['Measurement']['ThdAxis'] == 'Sync 0':
#                        print('One-color tiling in progress!')
                        self.statusText.setText('One-color tiling started, tile %d of %d' % (self.tilenumber+1, self.numberoftiles))
                        self.imspector.connect_end(self,1)
                        self.rowsperframe = self.measurementparams['NiDAQ6353'][':YRes']
#                        print(self.rowsperframe)
                    elif self.measurementparams['Measurement']['SecAxis'] == 'NiDAQ6353 DACs::4' and self.measurementparams['Measurement']['FthAxis'] == 'Sync 0':
#                        print('Two-color tiling in progress!')
                        self.statusText.setText('Two-color tiling started, tile %d of %d' % (1, self.numberoftiles))
                        self.imspector.connect_end(self,1)
                        # Use double the number of rows, as we are doing two-color imaging, and as such want to take the next tile when we have scanned 2*the whole frame
                        self.rowsperframe = 2*self.measurementparams['NiDAQ6353'][':YRes']
#                        print(self.rowsperframe)
                    else:
#                        print('Axises in Imspector are not properly set-up for a tiling. Double check your settings.')
                        self.statusText.setText('Axises in Imspector are not properly set-up for a tiling. Double check your settings.')
                        self.endtiling()
                        return
                else:
#                    print('Number of tiles and number of frames in Imspector or size of tile and size of frame in Imspector measurement do not agree!')
                    self.statusText.setText('Number of tiles and number of frames in Imspector or size of tile and size of frame in Imspector measurement do not agree. Double check your settings.')
                    self.endtiling()
                    return
            self.tilesxsteps = np.ones((int(self.tilesYEdit.text()), int(self.tilesXEdit.text())-1))
            self.tilesxstepstemp = np.ones((int(self.tilesYEdit.text()),1)) * (int(self.tilesXEdit.text())-1) * -1
            self.tilesxsteps = np.concatenate((self.tilesxsteps, self.tilesxstepstemp), axis=1)
            self.tilesxsteps = np.ndarray.flatten(self.tilesxsteps)
            print(self.tilesxsteps)
            
            self.tilesysteps = np.zeros((int(self.tilesYEdit.text()), int(self.tilesXEdit.text())-1))
            self.tilesystepstemp = np.ones((int(self.tilesYEdit.text()),1)) * 1
            self.tilesysteps = np.concatenate((self.tilesysteps, self.tilesystepstemp), axis=1)
            self.tilesysteps = np.ndarray.flatten(self.tilesysteps)
            self.tilesysteps[-1] = -(int(self.tilesYEdit.text()) - 1)
            print(self.tilesysteps)
            
            # print(self.tiles)
            # Lock the focus at the first position in the saved foci, if using the saved foci
            if self.tilingSavedFociVar:
                self.focusWidget.tilingStep(self.tilefoci[self.tilenumber])
        else:
            self.endtiling()

# TODO: This function has not changed at all.
    def nextframe(self):
        if self.tilingActiveVar:
            # print(self.tilesxsteps[self.tilenumber])
            # Save the current tiles focus, if the focuscheckvar is checked.
            if self.tilingFocusCheckVar:
                self.tilefoci[self.tilenumber] = self.focusWidget.getFocusPosition()
            # First unlock focus, if it is locked
            if self.focusWidget.locked:
                self.focusWidget.unlockFocus()
            # Move stage the tiling step distances required for the next step
            # Interchange X and Y to mimic Imspectors X and Y axes
            self.xystage.move_relY(float(self.tilestepsize * self.tilesxsteps[self.tilenumber]))
            self.xystage.move_relX(float(self.tilestepsize * self.tilesysteps[self.tilenumber]))
            # Check if the last step has been taken
            if self.tilenumber == self.numberoftiles-1:
                # If so, finish the tiling
#                print('Tiling is done!')
                self.endtiling()
                if self.tilingFocusCheckVar:
                    self.statusText.setText('Setting tiling foci done, start tiling by checking "Use saved focal planes" and clicking "Initialize tiling".')
                else:
                    self.statusText.setText('Tiling is done!')
            else:
                # If not, change the current tile number to the next tile,
                # and call the tilingStep function in the focus widget, to
                # unlock the focus and lock it anew.
                self.tilenumber = self.tilenumber + 1
                if self.tilingSavedFociVar:
                    self.focusWidget.tilingStep(self.tilefoci[self.tilenumber])
                else:
                    self.focusWidget.tilingStep()
                if self.tilingFocusCheckVar:
                    self.statusText.setText('Setting tiling foci, tile %d of %d' % (self.tilenumber+1, self.numberoftiles))

# TODO: This function has not changed at all.
    def endtimelapse(self):
        # Do all the things needed to be done when you finish or end a tiling
        self.tilingActiveVar = False
        self.initTilingButton.setText('Initialize tiling')
        self.tilenumber = 0
        self.imspector.disconnect_end(self, 1)

    def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)


if __name__ == '__main__':

    app = QtGui.QApplication([])

    win = TimelapseWidget()
    win.show()
    app.exec_()


# TODO: Understand how to use this class.
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
            self._timer = threading.Timer(self.next_call - time.time(), self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False
    
    