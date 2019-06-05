# -*- coding: utf-8 -*-

# import numpy as np
import os
import time

from pyqtgraph.Qt import QtCore, QtGui
# import pyqtgraph as pg
from pyqtgraph.dockarea import Dock, DockArea
# from pyqtgraph.console import ConsoleWidget

from lantz import Q_

# tormenta imports
import control.LaserWidget as LaserWidget
# import control.SignalGen as SignalGen
# import control.Scan as Scan
import control.focus as focus
import control.widefield as widefield
import control.tiling as tiling
# import control.molecules_counter as moleculesCounter
# import control.ontime as ontime
# import control.tableWidget as tableWidget
import control.slmWidget as slmWidget
import control.guitools as guitools
import specpy as sp

# Widget to control image or sequence recording. Recording only possible when liveview active.
# StartRecording called when "Rec" presset. Creates recording thread with RecWorker, recording is then
# done in this seperate thread.

datapath = u"C:\\Users\\aurelien.barbotin\Documents\Data\DefaultDataFolder"


class FileWarning(QtGui.QMessageBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class TempestaSLMKatanaGUI(QtGui.QMainWindow):
    """Main GUI class. This class calls other modules in the control folder

    :param Laser bluelaser: object controlling one laser
    :param Laser violetlaser: object controlling one laser
    :param Laser uvlaser: object controlling one laser
    :param Camera orcaflash: object controlling a CCD camera
    :param SLMdisplay slm: object controlling a SLM
    :param Scanner scanXY: object controlling a Marzhauser XY-scanning stage
    :param Scanner scanZ: object controlling a Piezoconcept Z-scanning inset
    """

    liveviewStarts = QtCore.pyqtSignal()
    liveviewEnds = QtCore.pyqtSignal()

    def __init__(self, bluelaser, violetlaser, uvlaser, slm, scanZ, scanXY,
                 webcamFocusLock, webcamWidefield, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # os.chdir('C:\\Users\\STEDred\Documents\TempestaSnapshots')

        self.violetlaser = violetlaser
        self.slm = slm
        self.scanZ = scanZ
        self.scanXY = scanXY
        self.imspector = sp.Imspector()
        self.filewarning = FileWarning()

        self.s = Q_(1, 's')
        self.lastTime = time.clock()
        self.fps = None

        # Actions in menubar
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')

        self.savePresetAction = QtGui.QAction('Save configuration...', self)
        self.savePresetAction.setShortcut('Ctrl+S')
        self.savePresetAction.setStatusTip('Save camera & recording settings')
        savePresetFunction = lambda: guitools.savePreset(self)
        self.savePresetAction.triggered.connect(savePresetFunction)
        fileMenu.addAction(self.savePresetAction)
        fileMenu.addSeparator()

        self.exportTiffAction = QtGui.QAction('Export HDF5 to Tiff...', self)
        self.exportTiffAction.setShortcut('Ctrl+E')
        self.exportTiffAction.setStatusTip('Export HDF5 file to Tiff format')
        self.exportTiffAction.triggered.connect(guitools.TiffConverterThread)
        fileMenu.addAction(self.exportTiffAction)

        self.exportlastAction = QtGui.QAction('Export last recording to Tiff',
                                              self)
        self.exportlastAction.setEnabled(False)
        self.exportlastAction.setShortcut('Ctrl+L')
        self.exportlastAction.setStatusTip('Export last recording to Tiff ' +
                                           'format')
        fileMenu.addAction(self.exportlastAction)
        fileMenu.addSeparator()

        exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(QtGui.QApplication.closeAllWindows)
        fileMenu.addAction(exitAction)

        self.presetsMenu = QtGui.QComboBox()
        self.presetDir = datapath
        if not(os.path.isdir(self.presetDir)):
            self.presetDir = os.path.join(os.getcwd(), 'control/Presets')
        for preset in os.listdir(self.presetDir):
            self.presetsMenu.addItem(preset)
        self.loadPresetButton = QtGui.QPushButton('Load preset')
        loadPresetFunction = lambda: guitools.loadPreset(self)
        self.loadPresetButton.pressed.connect(loadPresetFunction)

        # Dock widget
        dockArea = DockArea()

        # Laser Widget
        laserDock = Dock("Laser Control", size=(600, 500))
        self.lasers = (bluelaser, violetlaser, uvlaser)
        self.laserWidgets = LaserWidget.LaserWidget(self.lasers)
        laserDock.addWidget(self.laserWidgets)
        dockArea.addDock(laserDock)

        # SLM widget
        slmDock = Dock("SLM", size=(600, 300))
        self.slmWidget = slmWidget.slmWidget(self.slm)
        slmDock.addWidget(self.slmWidget)
        dockArea.addDock(slmDock, "right", laserDock)

        # Focus lock widget
        focusDock = Dock("Focus lock", size=(600, 500))
        self.focusWidget = focus.FocusWidget(self.scanZ, webcamFocusLock)
        focusDock.addWidget(self.focusWidget)
        dockArea.addDock(focusDock, "above", laserDock)

        # Widefield camera widget
        widefieldDock = Dock("Widefield", size=(600, 500))
        self.widefieldWidget = widefield.WidefieldWidget(webcamWidefield)
        widefieldDock.addWidget(self.widefieldWidget)
        dockArea.addDock(widefieldDock, "below", focusDock)

        # XY-scanner tiling widget
        tilingDock = Dock("Tiling", size=(600, 500))
        self.tilingWidget = tiling.TilingWidget(self.scanXY, self.focusWidget, self.imspector)
        tilingDock.addWidget(self.tilingWidget)
        dockArea.addDock(tilingDock, "below", widefieldDock)
        
        self.setWindowTitle('Tempesta - SLM and Katana laser control')
        self.cwidget = QtGui.QWidget()
        self.setCentralWidget(self.cwidget)

        # Widgets' layout
        layout = QtGui.QGridLayout()
        self.cwidget.setLayout(layout)
#        layout.setColumnMinimumWidth(0, 100)
#        layout.setColumnMinimumWidth(1, 350)
#        layout.setColumnMinimumWidth(2, 150)
#        layout.setColumnMinimumWidth(3, 200)
#        layout.setRowMinimumHeight(0, 350)
#        layout.setRowMinimumHeight(1, 350)
#        layout.setRowMinimumHeight(2, 350)
#        layout.setRowMinimumHeight(3, 30)
        layout.addWidget(dockArea, 0, 3, 5, 1)
#        layout.addWidget(self.scanxyWidget,0, 2, 5, 1)

#        layout.setRowMinimumHeight(2, 40)
#        layout.setColumnMinimumWidth(2, 1000)

    def closeEvent(self, *args, **kwargs):
        """closes the different devices. Resets the NiDaq card, turns off the lasers and cuts communication with the SLM"""
        try:
            self.lvthread.terminate()
        except:
            pass

        self.laserWidgets.closeEvent(*args, **kwargs)
        self.slmWidget.closeEvent(*args, **kwargs)

        super().closeEvent(*args, **kwargs)

if __name__ == "main":
    pass
