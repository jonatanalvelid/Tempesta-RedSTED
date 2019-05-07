# -*- coding: utf-8 -*-
"""
Created on Wed Apr 24 15:23:30 2019

@author: jonatan.alvelid
"""

# import os
import numpy as np
# import time
# import pyqtgraph as pg
from pyqtgraph.Qt import QtGui
# import pyqtgraph.ptime as ptime
# from lantz import Q_
# import control.pi as pi
# import control.instruments as instruments
# from instrumental import u
# import time


class TilingWidget(QtGui.QFrame):

    def __init__(self, xystage, focuswidget, main=None, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.setMinimumSize(2, 350)

        self.focusWidget = focuswidget
        self.main = main  # main va a ser RecordingWidget de control.py
        self.xystage = xystage
        self.tilingActiveVar = False  # boolean telling if tiling is active
        self.tilenumber = 0  # number of current tile (0 - (number of tiles-1))
        self.tilestepsize = 0  # tiling step distance

        self.movelengthXLabel = QtGui.QLabel('Move distance, X [um]')
        self.movelengthXEdit = QtGui.QLineEdit('0')
        self.movelengthYLabel = QtGui.QLabel('Move distance, Y [um]')
        self.movelengthYEdit = QtGui.QLineEdit('0')
        self.moveButton = QtGui.QPushButton('Move')
        self.moveButton.clicked.connect(self.movestage)
        # self.moveCenterButton = QtGui.QPushButton('Move to (0,0)')
        # self.moveCenterButton.clicked.connect(self.movecenter)
        
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

        # GUI layout
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.movelengthXLabel, 0, 0)
        grid.addWidget(self.movelengthXEdit, 1, 0)
        grid.addWidget(self.movelengthYLabel, 0, 1)
        grid.addWidget(self.movelengthYEdit, 1, 1)
        grid.addWidget(self.moveButton, 4, 0)
        # grid.addWidget(self.moveCenterButton, 4, 1)
        
        grid.addWidget(self.tilesXLabel, 0, 3)
        grid.addWidget(self.tilesXEdit, 1, 3)
        grid.addWidget(self.tilesYLabel, 0, 4)
        grid.addWidget(self.tilesYEdit, 1, 4)
        grid.addWidget(self.tilesSizeLabel, 2, 3)
        grid.addWidget(self.tilesSizeEdit, 3, 3)
        grid.addWidget(self.tilesMarginLabel, 2, 4)
        grid.addWidget(self.tilesMarginEdit, 3, 4)
        grid.addWidget(self.initTilingButton, 4, 3)
        grid.addWidget(self.nextTileButton, 4, 4)
        grid.addWidget(self.mockFocusButton, 5, 4)


    def movestage(self):
        #self.xystage.move_rel(float(self.movelengthXEdit.text()), float(self.movelengthYEdit.text()))
        self.xystage.move_relX(float(self.movelengthXEdit.text()))
        self.xystage.move_relY(float(self.movelengthYEdit.text()))

    # def movecenter(self):
    #     self.xystage.move_absX(float(0))
    #     self.xystage.move_absY(float(0))
        
    def inittiling(self):
        if self.tilingActiveVar == False:
            self.tilingActiveVar = True
            self.initTilingButton.setText('Reset/stop tiling')
            # Get the tile step distance in um, i.e. tile size minus margin
            self.tilestepsize = float(self.tilesSizeEdit.text()) - float(self.tilesMarginEdit.text())
            self.numberoftiles = int(self.tilesXEdit.text())*int(self.tilesYEdit.text())
            self.tilenumber = 0
            
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
            
            print(self.tiles)
        else:
            self.tilingActiveVar = False
            self.initTilingButton.setText('Initialize tiling')
            self.tilenumber = 0
            
    def nexttile(self):
        if self.tilingActiveVar == True:
            # print(self.tilesxsteps[self.tilenumber])
            # Move stage the tiling step distances required for the next step
            # Interchange X and Y to mimic Imspectors X and Y axes
            self.xystage.move_relY(float(self.tilestepsize * self.tilesxsteps[self.tilenumber]))
            self.xystage.move_relX(float(self.tilestepsize * self.tilesysteps[self.tilenumber]))
            # Check if the last step has been taken
            if self.tilenumber == self.numberoftiles-1:
                # If so, finish the tiling
                print('Tiling is done!')
                self.tilingActiveVar = False
                self.initTilingButton.setText('Initialize tiling')
                self.tilenumber = 0
            else:
                # If not, change the current tile number to the next tile,
                # and call the tilingStep function in the focus widget, to
                # unlock the focus and lock it anew.
                self.tilenumber = self.tilenumber + 1
                self.focusWidget.tilingStep()
            

    def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)


if __name__ == '__main__':

    app = QtGui.QApplication([])

    win = TilingWidget()
    win.show()
    app.exec_()
