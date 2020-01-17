# -*- coding: utf-8 -*-
"""
Created on Mon Jan 23 15:21:07 2017

@author: STEDred, jonatanalvelid
"""

# General imports
import os
#import time

# Scientific python packages and software imports
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.dockarea import Dock, DockArea
from lantz import Q_
import specpy as sp

# Tempesta control imports
from control import LaserWidget, focus, widefield, tiling, timelapse, slmWidget, guitools, motcorr

#DATAPATH = r"C:\\Users\\STEDred\Documents\defaultTempestaData"


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
        self.scan_z = scanZ
        self.aotf = aotf
        self.scan_xy = scanXY
        self.dmi8 = leicastand
        self.imspector = sp.Imspector()

        self.filewarning = FileWarning()

#        self.s = Q_(1, 's')
#        self.lastTime = time.clock()
        self.fps = None

#        # Potentially remove all this?
#        # Actions in menubar
#        menubar = self.menuBar()
#        file_menu = menubar.addMenu('&File')
#
#        self.savePresetAction = QtGui.QAction('Save configuration...', self)
#        self.savePresetAction.setShortcut('Ctrl+S')
#        self.savePresetAction.setStatusTip('Save camera & recording settings')
#        savePresetFunction = lambda: guitools.savePreset(self)
#        self.savePresetAction.triggered.connect(savePresetFunction)
#        file_menu.addAction(self.savePresetAction)
#        file_menu.addSeparator()
#
#        self.exportTiffAction = QtGui.QAction('Export HDF5 to Tiff...', self)
#        self.exportTiffAction.setShortcut('Ctrl+E')
#        self.exportTiffAction.setStatusTip('Export HDF5 file to Tiff format')
#        self.exportTiffAction.triggered.connect(guitools.TiffConverterThread)
#        file_menu.addAction(self.exportTiffAction)
#
#        self.exportlastAction = QtGui.QAction('Export last recording to Tiff',
#                                             self)
#        self.exportlastAction.setEnabled(False)
#        self.exportlastAction.setShortcut('Ctrl+L')
#        self.exportlastAction.setStatusTip('Export last recording to Tiff ' +
#                                           'format')
#        file_menu.addAction(self.exportlastAction)
#        file_menu.addSeparator()
#
#        exit_action = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
#        exit_action.setShortcut('Ctrl+Q')
#        exit_action.setStatusTip('Exit application')
#        exit_action.triggered.connect(QtGui.QApplication.closeAllWindows)
#       file_menu.addAction(exit_action)

#        # Potentially remove all this?
#        self.presetsMenu = QtGui.QComboBox()
#        self.presetDir = DATAPATH
#        if not(os.path.isdir(self.presetDir)):
#            self.presetDir = os.path.join(os.getcwd(), 'control\\Presets')
#        for preset in os.listdir(self.presetDir):
#            self.presetsMenu.addItem(preset)
#        self.loadPresetButton = QtGui.QPushButton('Load preset')
#        loadPresetFunction = lambda: guitools.loadPreset(self)
#        self.loadPresetButton.pressed.connect(loadPresetFunction)

        # Dock widget
        dock_area = DockArea()

        # Laser Widget
        laser_dock = Dock("Laser Control", size=(400, 500))
        self.lasers = stedlaser
        self.laser_widgets = LaserWidget.LaserWidget(self.lasers, self.aotf)
        laser_dock.addWidget(self.laser_widgets)
        dock_area.addDock(laser_dock, 'right')

        # SLM widget
        slm_dock = Dock("SLM", size=(400, 300))
        self.slm_widget = slmWidget.slmWidget(self.slm)
        slm_dock.addWidget(self.slm_widget)
        dock_area.addDock(slm_dock, "bottom", laser_dock)

        # Widefield camera widget
        widefield_dock = Dock("Widefield", size=(500, 500))
        self.widefield_widget = widefield.WidefieldWidget(webcamWidefield)
        widefield_dock.addWidget(self.widefield_widget)
        dock_area.addDock(widefield_dock, "left")

        # Focus lock widget
        focus_dock = Dock("Focus lock", size=(500, 500))
        self.focus_widget = focus.FocusWidget(self.scan_z, webcamFocusLock,
                                              self.imspector)
        focus_dock.addWidget(self.focus_widget)
        dock_area.addDock(focus_dock, "below", widefield_dock)

        # Timelapse widget
        timelapse_dock = Dock("Timelapse", size=(500, 200))
        self.timelapse_widget = timelapse.TimelapseWidget(self.imspector)
        timelapse_dock.addWidget(self.timelapse_widget)
        dock_area.addDock(timelapse_dock, "top", widefield_dock)

        # Objective mot_corr widget
        motcorr_dock = Dock("Glycerol motCORR", size=(500, 200))
        self.motcorr_widget = motcorr.MotcorrWidget(self.dmi8)
        motcorr_dock.addWidget(self.motcorr_widget)
        dock_area.addDock(motcorr_dock, "below", timelapse_dock)

        # XY-scanner tiling widget
        tiling_dock = Dock("Tiling", size=(500, 200))
        self.tiling_widget = tiling.TilingWidget(self.scan_xy, self.focusWidget,
                                                 self.imspector)
        tiling_dock.addWidget(self.tiling_widget)
        dock_area.addDock(tiling_dock, "below", timelapse_dock)


        self.setWindowTitle('Tempesta - RedSTED edition')
        self.cwidget = QtGui.QWidget()
        self.setCentralWidget(self.cwidget)

        # Widgets' layout
        layout = QtGui.QGridLayout()
        self.cwidget.setLayout(layout)
        layout.addWidget(dock_area, 0, 3, 5, 1)

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
