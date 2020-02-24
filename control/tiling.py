# -*- coding: utf-8 -*-
"""
Created on Wed Apr 24 15:23:30 2019

@author: jonatan.alvelid
"""

import numpy as np
from pyqtgraph.Qt import QtCore, QtGui


class TilingWidget(QtGui.QFrame):

    def __init__(self, xystage, focuswidget, imspector, main=None, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.setMinimumSize(200, 200)  # Set the minimum size of the widget

        self.xystage = xystage
        self.focusWidget = focuswidget
        self.imspector = imspector
        self.main = main
        self.tilingActiveVar = False  # boolean telling if tiling is active
        self.tilingFocusCheckVar = False  # boolean telling if curr til run is to set focus lock positions
        self.tilingSavedFociVar = False  # boolean telling if to tile with the previously saved foci planes
        self.automaticTilingVar = False  # boolean telling if you do fully automatic tiling
        self.tilenumber = 0  # number of current tile (0 - (number of tiles-1))
        self.tilestepsize = 0  # tiling step distance
        self.tilefoci = np.zeros(1)  # use this array to store foci points for the tiles, initiate anew on a new tile focus check scan
        self.countrows = 0  # number of rows scanned in Imspector
        self.rowsperframe = 0  # number of rows per frame in Imspector measurement
        joystick_update_time = 200  # (ms) update rate of the joyst functionbut

        self.movelengthXLabel = QtGui.QLabel('Move distance, X [um]')
        self.movelengthXEdit = QtGui.QLineEdit('0')
        self.movelengthYLabel = QtGui.QLabel('Move distance, Y [um]')
        self.movelengthYEdit = QtGui.QLineEdit('0')
        self.moveButton = QtGui.QPushButton('Move')
        self.moveButton.clicked.connect(self.movestage)
        # The below button was dangerous, as the 0,0 is never really in the
        # middle of the sample, and hence can move the stage to a position
        # off-sample. Could be useful if we "redefine" 0,0 to be the middle
        # of the sample by a manual button press, and then you would be
        # limited to just move inside the sample, not outside! Necessary?
        # self.moveCenterButton = QtGui.QPushButton('Move to (0,0)')
        # self.moveCenterButton.clicked.connect(self.movecenter)

        self.tilingFocusCheckBox = QtGui.QCheckBox('Decide focal planes for tiles')
        self.tilingFocusCheckBox.stateChanged.connect(self.tilingFocusCheckVarChange)
        self.tilingSavedFociCheckBox = QtGui.QCheckBox('Use saved focal planes for tiling')
        self.tilingSavedFociCheckBox.stateChanged.connect(self.tilingSavedFociVarChange)
        self.automaticTilingCheckBox = QtGui.QCheckBox('Do fully automatic tiling')
        self.automaticTilingCheckBox.stateChanged.connect(self.automaticTilingVarChange)

        self.tilesXLabel = QtGui.QLabel('Number of tiles, X')
        self.tilesXEdit = QtGui.QLineEdit('1')
        self.tilesYLabel = QtGui.QLabel('Number of tiles, Y')
        self.tilesYEdit = QtGui.QLineEdit('1')
        self.tilesSizeLabel = QtGui.QLabel('Size of tiles [um]')
        self.tilesSizeEdit = QtGui.QLineEdit('50')
        self.tilesMarginLabel = QtGui.QLabel('Tile margin size [um]')
        self.tilesMarginEdit = QtGui.QLineEdit('5')
        self.initTilingButton = QtGui.QPushButton('Initialize tiling')
        self.initTilingButton.clicked.connect(self.inittiling)
        self.nextTileButton = QtGui.QPushButton('Next tile')
        self.nextTileButton.clicked.connect(self.nexttile)

        self.mockFocusButton = QtGui.QPushButton('Mock focus')
        self.mockFocusButton.clicked.connect(self.focusWidget.tilingStep)

        # Add status bar, a non-editable text, that tells the current state
        self.statusLabel = QtGui.QLabel('Status:')
        self.statusText = QtGui.QLineEdit(
                'Click "Initialize tiling" to start tiling acquisition')
        self.statusText.setReadOnly(True)
        
        # Thread for checking if joystick function buttons are pressed
        self.joystick_read_thread = JoystickReadThread(self)
        self.joystick_read_thread.start()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.joystick_read_thread.update)
        self.timer.start(joystick_update_time)

        # GUI layout
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.movelengthXLabel, 0, 0)
        grid.addWidget(self.movelengthYLabel, 0, 1)
        grid.addWidget(self.tilesXLabel, 0, 3)
        grid.addWidget(self.tilesYLabel, 0, 4)

        grid.addWidget(self.movelengthXEdit, 1, 0)
        grid.addWidget(self.movelengthYEdit, 1, 1)
        grid.addWidget(self.tilesXEdit, 1, 3)
        grid.addWidget(self.tilesYEdit, 1, 4)

        grid.addWidget(self.tilesSizeLabel, 2, 3)
        grid.addWidget(self.tilesMarginLabel, 2, 4)

        grid.addWidget(self.tilesSizeEdit, 3, 3)
        grid.addWidget(self.tilesMarginEdit, 3, 4)

        grid.addWidget(self.moveButton, 4, 0)
        grid.addWidget(self.initTilingButton, 4, 3)
        grid.addWidget(self.nextTileButton, 4, 4)

        grid.addWidget(self.mockFocusButton, 5, 0)
        grid.addWidget(self.tilingFocusCheckBox, 5, 3)
        grid.addWidget(self.tilingSavedFociCheckBox, 5, 4)
        grid.addWidget(self.automaticTilingCheckBox, 5, 2)

        grid.addWidget(self.statusLabel, 6, 0, 1, 1)
        grid.addWidget(self.statusText, 6, 1, 1, 4)

        # grid.addWidget(self.moveCenterButton, 4, 1)

    def __call__(self):
        self.countrows = self.countrows + 1
        if self.countrows == self.rowsperframe:
#            print('Next tile!')
            self.countrows = 0
            self.nexttile()
            self.statusText.setText('Tiling in progress, tile %d of %d' %
                                    (self.tilenumber + 1, self.numberoftiles))
            # frame is finished, move to next tile in a good way!

    def tilingFocusCheckVarChange(self):
        if self.tilingFocusCheckVar:
            self.tilingFocusCheckVar = False
        else:
            self.tilingFocusCheckVar = True

    def tilingSavedFociVarChange(self):
        if self.tilingSavedFociVar:
            self.tilingSavedFociVar = False
        else:
            self.tilingSavedFociVar = True

    def automaticTilingVarChange(self):
        if self.automaticTilingVar:
            self.automaticTilingVar = False
        else:
            self.automaticTilingVar = True

    def movestage(self):
        #self.xystage.move_rel(float(self.movelengthXEdit.text()), float(self.movelengthYEdit.text()))
        self.xystage.move_relX(float(self.movelengthXEdit.text()))
        self.xystage.move_relY(float(self.movelengthYEdit.text()))

    # def movecenter(self):
    #     self.xystage.move_absX(float(0))
    #     self.xystage.move_absY(float(0))

    def inittiling(self):
        if not self.tilingActiveVar:
            self.tilingActiveVar = True
            self.initTilingButton.setText('Reset/stop tiling')
            # Get the tile step distance in um, i.e. tile size minus margin
            self.tilestepsize = float(self.tilesSizeEdit.text()) - \
                float(self.tilesMarginEdit.text())
            self.numberoftiles = int(self.tilesXEdit.text()) * \
                int(self.tilesYEdit.text())
            self.tilenumber = 0
            # Create a new tilefoci-array if this is a new focus check tiling
            if self.tilingFocusCheckVar:
                self.tilefoci = np.zeros(self.numberoftiles)
                self.statusText.setText('Setting tiling foci, tile %d of %d'
                                        % (self.tilenumber+1, self.numberoftiles))
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
                if self.measurementparams['Sync']['0Res'] == self.numberoftiles \
                and self.measurementparams['NiDAQ6353'][':YLen'] == float(self.tilesSizeEdit.text()) \
                and round(self.measurementparams['NiDAQ6353'][':XLen']) == float(self.tilesSizeEdit.text()):
                    if self.measurementparams['Measurement']['ThdAxis'] == 'Sync 0':
#                        print('One-color tiling in progress!')
                        self.statusText.setText('One-color tiling started, tile %d of %d' % (self.tilenumber+1, self.numberoftiles))
                        self.imspector.connect_end(self,1)
                        self.rowsperframe = self.measurementparams['NiDAQ6353'][':YRes']
#                        print(self.rowsperframe)
                    elif self.measurementparams['Measurement']['SecAxis'] == 'NiDAQ6353 DACs::4' \
                    and self.measurementparams['Measurement']['FthAxis'] == 'Sync 0':
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
            self.tilesxsteps = np.ones((int(self.tilesYEdit.text()),
                                        int(self.tilesXEdit.text())-1))
            self.tilesxstepstemp = np.ones((int(self.tilesYEdit.text()), 1)) *\
                (int(self.tilesXEdit.text())-1) * -1
            self.tilesxsteps = np.concatenate((self.tilesxsteps,
                                               self.tilesxstepstemp), axis=1)
            self.tilesxsteps = np.ndarray.flatten(self.tilesxsteps)
            print(self.tilesxsteps)

            self.tilesysteps = np.zeros((int(self.tilesYEdit.text()),
                                         int(self.tilesXEdit.text()) - 1))
            self.tilesystepstemp = np.ones((int(self.tilesYEdit.text()), 1))
            self.tilesysteps = np.concatenate((self.tilesysteps,
                                               self.tilesystepstemp), axis=1)
            self.tilesysteps = np.ndarray.flatten(self.tilesysteps)
            self.tilesysteps[-1] = -(int(self.tilesYEdit.text()) - 1)
            print(self.tilesysteps)
            
            # print(self.tiles)
            # Lock the focus at the first position in the saved foci, if using the saved foci
            if self.tilingSavedFociVar:
                self.focusWidget.tilingStep(self.tilefoci[self.tilenumber])
        else:
            self.endtiling()

    def nexttile(self):
        if self.tilingActiveVar:
            # print(self.tilesxsteps[self.tilenumber])
            # Save the current tiles focus, if the focuscheckvar is checked.
            if self.tilingFocusCheckVar:
                self.tilefoci[self.tilenumber] = \
                    self.focusWidget.getFocusPosition()
            # First unlock focus, if it is locked
            if self.focusWidget.locked:
                self.focusWidget.unlockFocus()
            # Move stage the tiling step distances required for the next step
            # Interchange X and Y to mimic Imspectors X and Y axes
            self.xystage.move_relY(float(self.tilestepsize *
                                         self.tilesxsteps[self.tilenumber]))
            self.xystage.move_relX(float(self.tilestepsize *
                                         self.tilesysteps[self.tilenumber]))
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

    def endtiling(self):
        # Do all the things needed to be done when you finish or end a tiling
        self.tilingActiveVar = False
        self.initTilingButton.setText('Initialize tiling')
        self.tilenumber = 0
        self.imspector.disconnect_end(self, 1)

    def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)


class JoystickReadThread(QtCore.QThread):

    def __init__(self, tiling_widget, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.xystage = tiling_widget.xystage
        fovsize = 200
        self.move_dist = [-fovsize, -fovsize, fovsize, fovsize]

    def update(self):
        button_status = self.xystage.function_press()
        for button, buttonval in enumerate(button_status):
            if buttonval == 1:
                print(button)
                if button == 0 or button == 2:
                    self.xystage.move_relY(self.move_dist[button])
                elif button == 1 or button == 3:
                    self.xystage.move_relX(self.move_dist[button])


if __name__ == '__main__':

    app = QtGui.QApplication([])

    win = TilingWidget()
    win.show()
    app.exec_()
