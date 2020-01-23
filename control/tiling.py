# -*- coding: utf-8 -*-
"""
Created on Wed Apr 24 15:23:30 2019

@author: jonatan.alvelid
"""

import numpy as np
from pyqtgraph.Qt import QtGui


class TilingWidget(QtGui.QFrame):
    """Widget to take care of the tiled imaging."""
    def __init__(self, xystage, focus_widget, imspector, main=None, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.setMinimumSize(200, 200)  # Set the minimum size of the widget

        self.xystage = xystage
        self.focus_widget = focus_widget
        self.imspector = imspector
        self.main = main
        self.tiling_active_var = False  # bool telling if tiling is active
        self.tiling_focus_check_var = False  # bool telling if curr til run is setting foc lock pos
        self.tiling_saved_foci_var = False  # bool telling if to tile with the saved foci planes
        self.automatic_tiling_var = False  # bool telling if you do fully automatic tiling
        self.numberoftiles = 0  # number of tiles to scan
        self.tilenumber = 0  # number of current tile (0 - (number of tiles-1))
        self.tilestepsize = 0  # tiling step distance
        self.tilefoci = np.zeros(1)  # use this array to store foci points for the tiles
        self.countrows = 0  # number of rows scanned in Imspector
        self.rowsperframe = 0  # number of rows per frame in Imspector measurement
        self.tiles_x_steps = np.ones(1,1)  # steps to take in the x direction for each tile
        self.tiles_y_steps = np.ones(1,1)  # step to take in the y direction for each tile

        self.movelength_x_label = QtGui.QLabel('Move distance, X [um]')
        self.movelength_x_edit = QtGui.QLineEdit('0')
        self.movelength_y_label = QtGui.QLabel('Move distance, Y [um]')
        self.movelength_y_edit = QtGui.QLineEdit('0')
        self.move_button = QtGui.QPushButton('Move')
        self.move_button.clicked.connect(self.movestage)
        # The below button was dangerous, as the 0,0 is never really in the
        # middle of the sample, and hence can move the stage to a position
        # off-sample. Could be useful if we "redefine" 0,0 to be the middle
        # of the sample by a manual button press, and then you would be
        # limited to just move inside the sample, not outside! Necessary?
        # self.moveCenterButton = QtGui.QPushButton('Move to (0,0)')
        # self.moveCenterButton.clicked.connect(self.movecenter)

        self.tiling_focus_check_box = QtGui.QCheckBox('Decide focal planes for tiles')
        self.tiling_focusCheck_box.stateChanged.connect(self.tiling_focus_check_var_change)
        self.tiling_saved_foci_check_box = QtGui.QCheckBox('Use saved focal planes for tiling')
        self.tiling_saved_foci_check_box.stateChanged.connect(self.tiling_saved_foci_var_change)
        self.automatic_tiling_check_box = QtGui.QCheckBox('Do fully automatic tiling')
        self.automatic_tiling_check_box.stateChanged.connect(self.automatic_tiling_var_change)

        self.tiles_x_label = QtGui.QLabel('Number of tiles, X')
        self.tiles_x_edit = QtGui.QLineEdit('1')
        self.tiles_y_label = QtGui.QLabel('Number of tiles, Y')
        self.tiles_y_edit = QtGui.QLineEdit('1')
        self.tiles_size_label = QtGui.QLabel('Size of tiles [um]')
        self.tiles_size_edit = QtGui.QLineEdit('50')
        self.tiles_margin_label = QtGui.QLabel('Tile margin size [um]')
        self.tiles_margin_edit = QtGui.QLineEdit('5')
        self.init_tiling_button = QtGui.QPushButton('Initialize tiling')
        self.init_tiling_button.clicked.connect(self.inittiling)
        self.next_tile_button = QtGui.QPushButton('Next tile')
        self.next_tile_button.clicked.connect(self.nexttile)

        #self.mockFocusButton = QtGui.QPushButton('Mock focus')
        #self.mockFocusButton.clicked.connect(self.focus_widget.tilingStep)

        # Add status bar, a non-editable text, that tells the current state
        self.status_label = QtGui.QLabel('Status:')
        self.status_text = QtGui.QLineEdit(
            'Click "Initialize tiling" to start tiling acquisition')
        self.status_text.setReadOnly(True)

        # GUI layout
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.movelength_x_label, 0, 0)
        grid.addWidget(self.movelength_y_label, 0, 1)
        grid.addWidget(self.tiles_x_label, 0, 3)
        grid.addWidget(self.tiles_y_label, 0, 4)

        grid.addWidget(self.movelength_x_edit, 1, 0)
        grid.addWidget(self.movelength_y_edit, 1, 1)
        grid.addWidget(self.tiles_x_edit, 1, 3)
        grid.addWidget(self.tiles_y_edit, 1, 4)

        grid.addWidget(self.tiles_size_label, 2, 3)
        grid.addWidget(self.tiles_margin_abel, 2, 4)

        grid.addWidget(self.tiles_size_edit, 3, 3)
        grid.addWidget(self.tiles_margin_edit, 3, 4)

        grid.addWidget(self.move_button, 4, 0)
        grid.addWidget(self.init_tiling_button, 4, 3)
        grid.addWidget(self.next_tile_button, 4, 4)

        #grid.addWidget(self.mockFocusButton, 5, 0)
        grid.addWidget(self.tiling_focus_check_box, 5, 3)
        grid.addWidget(self.tiling_saved_foci_check_box, 5, 4)
        grid.addWidget(self.automatic_tiling_check_box, 5, 2)

        grid.addWidget(self.status_label, 6, 0, 1, 1)
        grid.addWidget(self.status_text, 6, 1, 1, 4)

        # grid.addWidget(self.moveCenterButton, 4, 1)

    def __call__(self):
        self.countrows = self.countrows + 1
        if self.countrows == self.rowsperframe:
            self.countrows = 0
            self.nexttile()
            self.status_text.setText('Tiling in progress, tile %d of %d' %
                                     (self.tilenumber + 1, self.numberoftiles))
            # frame is finished, move to next tile in a good way!

    def tiling_focus_check_var_change(self):
        """Change the tiling focus variable with a checkbox."""
        if self.tiling_focus_check_var:
            self.tiling_focus_check_var = False
        else:
            self.tiling_focus_check_var = True

    def tiling_saved_foci_var_change(self):
        """Change the saved tiling foci variable with a checkbox."""
        if self.tiling_saved_foci_var:
            self.tiling_saved_foci_var = False
        else:
            self.tiling_saved_foci_var = True

    def automatic_tiling_var_change(self):
        """Change the automatic tiling variable with a checkbox."""
        if self.automatic_tiling_var:
            self.automatic_tiling_var = False
        else:
            self.automatic_tiling_var = True

    def movestage(self):
        """Move the stage in X and Y."""
        self.xystage.move_relX(float(self.movelength_x_edit.text()))
        self.xystage.move_relY(float(self.movelength_y_edit.text()))

    def inittiling(self):
        """Initialize a tiling."""
        if not self.tiling_active_var:
            self.tiling_active_var = True
            self.init_tiling_button.setText('Reset/stop tiling')
            # Get the tile step distance in um, i.e. tile size minus margin
            self.tilestepsize = float(self.tiles_size_edit.text()) - \
                float(self.tilesMarginEdit.text())
            self.numberoftiles = int(self.tiles_x_edit.text()) * \
                int(self.tiles_y_edit.text())
            self.tilenumber = 0
            # Create a new tilefoci-array if this is a new focus check tiling
            if self.tiling_focus_check_var:
                self.tilefoci = np.zeros(self.numberoftiles)
                self.status_text.setText('Setting tiling foci, tile %d of %d'
                                         % (self.tilenumber+1, self.numberoftiles))
            else:
                print(self.tilefoci)
            # If you want to do automatic tiling, check number of rows in active imspector window
            # also connect the end of the frame-signal to the __call__ function
            if self.automatic_tiling_var:
                im_measurement = self.imspector.active_measurement()
                measurement_params = im_measurement.parameters('')
                # Check if measurement in imspector is stack with third axis as Sync 0 axis
                # Check if number of frames in Sync 0 is matchin the number of tiles!
                # Check if size of the tiles equals the size of the measurement in Imepsctor
                if measurement_params['Sync']['0Res'] == self.numberoftiles \
                and measurement_params['NiDAQ6353'][':YLen'] == float(self.tiles_size_edit.text()) \
                and round(measurement_params['NiDAQ6353'][':XLen']) == float(self.tiles_size_edit.text()):
                    if measurement_params['Measurement']['ThdAxis'] == 'Sync 0':
                        self.status_text.setText('One-color tiling started, tile %d of %d' % (self.tilenumber+1, self.numberoftiles))
                        self.imspector.connect_end(self, 1)
                        self.rowsperframe = measurement_params['NiDAQ6353'][':YRes']
                    elif measurement_params['Measurement']['SecAxis'] == 'NiDAQ6353 DACs::4' \
                    and measurement_params['Measurement']['FthAxis'] == 'Sync 0':
                        self.status_text.setText('Two-color tiling started, tile %d of %d' % (1, self.numberoftiles))
                        self.imspector.connect_end(self, 1)
                        # Use double the number of rows, as we are doing two-color imaging
                        self.rowsperframe = 2*measurement_params['NiDAQ6353'][':YRes']
                    else:
                        self.status_text.setText('Axises in Imspector are not properly set-up for a tiling. Double check your settings.')
                        self.endtiling()
                        return
                else:
                    self.status_text.setText('Number of tiles and number of frames in Imspector or size of tile and size of frame in Imspector measurement do not agree. Double check your settings.')
                    self.endtiling()
                    return
            self.tiles_x_steps = np.ones((int(self.tiles_y_edit.text()),
                                          int(self.tiles_x_edit.text()) - 1))
            tiles_x_steps_temp = np.ones((int(self.tiles_y_edit.text()), 1)) *\
                (int(self.tiles_x_edit.text())-1) * -1
            self.tiles_x_steps = np.concatenate((self.tiles_x_steps,
                                                 tiles_x_steps_temp), axis=1)
            self.tiles_x_steps = np.ndarray.flatten(self.tiles_x_steps)
            print(self.tiles_x_steps)

            self.tiles_y_steps = np.zeros((int(self.tiles_y_edit.text()),
                                           int(self.tiles_x_edit.text()) - 1))
            tiles_y_steps_temp = np.ones((int(self.tiles_y_edit.text()), 1))
            self.tiles_y_steps = np.concatenate((self.tiles_y_steps,
                                                 tiles_y_steps_temp), axis=1)
            self.tiles_y_steps = np.ndarray.flatten(self.tiles_y_steps)
            self.tiles_y_steps[-1] = -(int(self.tiles_y_edit.text()) - 1)
            print(self.tiles_y_steps)

            # print(self.tiles)
            # Lock the focus at the first position in the saved foci, if using the saved foci
            if self.tiling_saved_foci_var:
                self.focus_widget.tilingStep(self.tilefoci[self.tilenumber])
        else:
            self.endtiling()

    def nexttile(self):
        """Move to the next defined tile in the tiling process."""
        if self.tiling_active_var:
            # print(self.tiles_x_steps[self.tilenumber])
            # Save the current tiles focus, if the focuscheckvar is checked.
            if self.tiling_focus_check_var:
                self.tilefoci[self.tilenumber] = \
                    self.focus_widget.getFocusPosition()
            # First unlock focus, if it is locked
            if self.focus_widget.locked:
                self.focus_widget.unlockFocus()
            # Move stage the tiling step distances required for the next step
            # Interchange X and Y to mimic Imspectors X and Y axes
            self.xystage.move_relY(float(self.tilestepsize *
                                         self.tiles_x_steps[self.tilenumber]))
            self.xystage.move_relX(float(self.tilestepsize *
                                         self.tiles_y_steps[self.tilenumber]))
            # Check if the last step has been taken
            if self.tilenumber == self.numberoftiles-1:
                # If so, finish the tiling
#                print('Tiling is done!')
                self.endtiling()
                if self.tiling_focus_check_var:
                    self.status_text.setText('Setting tiling foci done, start tiling by checking "Use saved focal planes" and clicking "Initialize tiling".')
                else:
                    self.status_text.setText('Tiling is done!')
            else:
                # If not, change the current tile number to the next tile,
                # and call the tilingStep function in the focus widget, to
                # unlock the focus and lock it anew.
                self.tilenumber = self.tilenumber + 1
                if self.tiling_saved_foci_var:
                    self.focus_widget.tilingStep(self.tilefoci[self.tilenumber])
                else:
                    self.focus_widget.tilingStep()
                if self.tiling_focus_check_var:
                    self.status_text.setText('Setting tiling foci, tile %d of %d' % (self.tilenumber+1, self.numberoftiles))

    def endtiling(self):
        """End the tiling."""
        # Do all the things needed to be done when you finish or end a tiling
        self.tiling_active_var = False
        self.init_tiling_button.setText('Initialize tiling')
        self.tilenumber = 0
        self.imspector.disconnect_end(self, 1)

    def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)


if __name__ == '__main__':

    app = QtGui.QApplication([])

    win = TilingWidget()
    win.show()
    app.exec_()
