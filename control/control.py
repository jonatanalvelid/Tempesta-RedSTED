# -*- coding: utf-8 -*-
"""
Created on Mon Jan 23 15:21:07 2017

@author: STEDred, jonatanalvelid
"""

# General imports
import os
import time

# Scientific python packages and software imports
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.dockarea import Dock, DockArea
from lantz import Q_
import specpy as sp

# Tempesta control imports
import control.LaserWidget as LaserWidget
import control.focus as focus
import control.widefield as widefield
import control.tiling as tiling
import control.timelapse as timelapse
import control.slmWidget as slmWidget
import control.guitools as guitools
import control.motcorr as motcorr

datapath = r"C:\\Users\\STEDred\Documents\defaultTempestaData"


class FileWarning(QtGui.QMessageBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class TempestaSLMKatanaGUI(QtGui.QMainWindow):
    """Main GUI class. This class calls other modules in the control folder

    :param Laser greenlaser: object controlling one laser
    :param Laser redlaser: object controlling one laser
    :param Laser stedlaser: object controlling one laser
    :param Camera orcaflash: object controlling a CCD camera
    :param SLMdisplay slm: object controlling a SLM
    :param Scanner scanXY: object controlling a Marzhauser XY-scanning stage
    :param Scanner scanZ: object controlling a Piezoconcept Z-scanning inset
    """

    liveviewStarts = QtCore.pyqtSignal()
    liveviewEnds = QtCore.pyqtSignal()

    def __init__(self, stedlaser, slm, scanZ, scanXY, webcamFocusLock,
                 webcamWidefield, aotf, leicastand, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # os.chdir('C:\\Users\\STEDred\Documents\TempestaSnapshots')

        self.slm = slm
        self.scanZ = scanZ
        self.aotf = aotf
        self.scanXY = scanXY
        self.dmi8 = leicastand
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

        # Potentially remove all this?
        self.presetsMenu = QtGui.QComboBox()
        self.presetDir = datapath
        if not(os.path.isdir(self.presetDir)):
            self.presetDir = os.path.join(os.getcwd(), 'control\\Presets')
        for preset in os.listdir(self.presetDir):
            self.presetsMenu.addItem(preset)
        self.loadPresetButton = QtGui.QPushButton('Load preset')
        loadPresetFunction = lambda: guitools.loadPreset(self)
        self.loadPresetButton.pressed.connect(loadPresetFunction)

        # Dock widget
        dockArea = DockArea()

        # Laser Widget
        laserDock = Dock("Laser Control", size=(400, 500))
        self.lasers = stedlaser
        self.laserWidgets = LaserWidget.LaserWidget(self.lasers, self.aotf)
        laserDock.addWidget(self.laserWidgets)
        dockArea.addDock(laserDock, 'right')

        # SLM widget
        slmDock = Dock("SLM", size=(400, 300))
        self.slmWidget = slmWidget.slmWidget(self.slm)
        slmDock.addWidget(self.slmWidget)
        dockArea.addDock(slmDock, "bottom", laserDock)

        # Widefield camera widget
        widefieldDock = Dock("Widefield", size=(500, 500))
        self.widefieldWidget = widefield.WidefieldWidget(webcamWidefield)
        widefieldDock.addWidget(self.widefieldWidget)
        dockArea.addDock(widefieldDock, "left")

        # Focus lock widget
        focusDock = Dock("Focus lock", size=(500, 500))
        self.focusWidget = focus.FocusWidget(self.scanZ, webcamFocusLock,
                                             self.imspector)
        focusDock.addWidget(self.focusWidget)
        dockArea.addDock(focusDock, "below", widefieldDock)
        
        # Timelapse widget
        timelapseDock = Dock("Timelapse", size=(500, 200))
        self.timelapseWidget = timelapse.TimelapseWidget(self.imspector)
        timelapseDock.addWidget(self.timelapseWidget)
        dockArea.addDock(timelapseDock, "top", widefieldDock)
        
        # Objective mot_corr widget
        motcorrDock = Dock("Glycerol motCORR", size=(500, 200))
        self.MotcorrWidget = motcorr.MotcorrWidget(self.dmi8)
        motcorrDock.addWidget(self.MotcorrWidget)
        dockArea.addDock(motcorrDock, "below", timelapseDock)
        
        # XY-scanner tiling widget
        tilingDock = Dock("Tiling", size=(500, 200))
        self.tilingWidget = tiling.TilingWidget(self.scanXY, self.focusWidget,
                                                self.imspector)
        tilingDock.addWidget(self.tilingWidget)
        dockArea.addDock(tilingDock, "below", timelapseDock)


        self.setWindowTitle('Tempesta - RedSTED edition')
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
        """closes the different devices. Resets the NiDaq card,
        turns off the lasers and cuts communication with the SLM"""
        try:
            self.lvthread.terminate()
        except:
            pass

        self.laserWidgets.closeEvent(*args, **kwargs)
        self.slmWidget.closeEvent(*args, **kwargs)

        super().closeEvent(*args, **kwargs)


if __name__ == "main":
    pass
