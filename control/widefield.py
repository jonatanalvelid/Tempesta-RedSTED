# -*- coding: utf-8 -*-
"""
Created on Fri Sep 28 17:51:28 2018

@author: jonatan.alvelid
"""

import numpy as np
# import time
# import threading
import scipy.ndimage as ndi
from skimage.transform import resize
# from skimage.feature import peak_local_max
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
# import pyqtgraph.ptime as ptime
# from lantz import Q_
# import control.pi as pi
# import control.instruments as instruments
# from instrumental import u
import time


class WidefieldWidget(QtGui.QFrame):

    def __init__(self, webcam, main=None, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.setMinimumSize(2, 350)

        self.main = main  # main va a ser RecordingWidget de control.py
        self.webcam = webcam
        self.setPoint = 0
        self.n = 1
        self.max_dev = 0
        self.scansPerS = 15
        self.frameTime = 1000 / self.scansPerS
        self.camOnVar = False

        self.camDialogButton = QtGui.QPushButton('Camera Dialog')
        self.camDialogButton.clicked.connect(self.webcam.show_dialog)
        self.camOnBox = QtGui.QCheckBox('Camera on')

        # Widefield webcam graph widget
        self.webcamGraph = WebcamGraph()

        # Thread for getting the data and processing it
        self.processDataThread = ProcessDataThread(self)
        self.processDataThread.start()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.processDataThread.update)
        self.timer.start(self.frameTime)

        # GUI layout
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.webcamGraph, 0, 0, 4, 5)
        grid.addWidget(self.camDialogButton, 4, 2, 1, 5)
        grid.addWidget(self.camOnBox, 4, 1)

#        grid.setColumnMinimumWidth(1, 100)
#        grid.setColumnMinimumWidth(2, 40)
#        grid.setColumnMinimumWidth(0, 100)

        self.camOnBox.stateChanged.connect(self.camOnVarChange)

    def camOnVarChange(self):
        if self.camOnVar:
            self.camOnVar = False
        else:
            self.camOnVar = True

    def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)


class ProcessDataThread(QtCore.QThread):

    def __init__(self, widefieldWidget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widefieldWidget = widefieldWidget
        # Set-up the camera settings
        self.webcam = self.widefieldWidget.webcam
        self.ws = {'vsub': 4, 'hsub': 4,
                   'top': None, 'bot': None,
                   'exposure_time': 10}
        # Grab camera image
        self.image = self.webcam.grab_image()
        self.sensorSize = np.array(self.image.shape)

    def update(self):
        if self.widefieldWidget.camOnVar:
            try:
                # then = time.time()
                self.image = self.webcam.grab_image()
                # now = time.time()
                # print("WF: Whole grab image took: ", now-then, " seconds")
                # print("")
            except:
                pass
            # imagearray = np.array(self.image)
            # imagearray = resize(imagearray, (256, 320))
            # imagearraygf = ndi.filters.gaussian_filter(imagearray, 3)  # Gaussian filter the image, to remove noise.
            self.widefieldWidget.webcamGraph.update(self.image)


class WebcamGraph(pg.GraphicsWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mapcolors = np.array([[0.0417, 0, 0],
                                      [0.0833, 0, 0],
                                      [0.1250, 0, 0],
                                      [0.1667, 0, 0],
                                      [0.2083, 0, 0],
                                      [0.2500, 0, 0],
                                      [0.2917, 0, 0],
                                      [0.3333, 0, 0],
                                      [0.3750, 0, 0],
                                      [0.4167, 0, 0],
                                      [0.4583, 0, 0],
                                      [0.5000, 0, 0],
                                      [0.5417, 0, 0],
                                      [0.5833, 0, 0],
                                      [0.6250, 0, 0],
                                      [0.6667, 0, 0],
                                      [0.7083, 0, 0],
                                      [0.7500, 0, 0],
                                      [0.7917, 0, 0],
                                      [0.8333, 0, 0],
                                      [0.8750, 0, 0],
                                      [0.9167, 0, 0],
                                      [0.9583, 0, 0],
                                      [1.0000, 0, 0],
                                      [1.0000, 0.0417, 0],
                                      [1.0000, 0.0833, 0],
                                      [1.0000, 0.1250, 0],
                                      [1.0000, 0.1667, 0],
                                      [1.0000, 0.2083, 0],
                                      [1.0000, 0.2500, 0],
                                      [1.0000, 0.2917, 0],
                                      [1.0000, 0.3333, 0],
                                      [1.0000, 0.3750, 0],
                                      [1.0000, 0.4167, 0],
                                      [1.0000, 0.4583, 0],
                                      [1.0000, 0.5000, 0],
                                      [1.0000, 0.5417, 0],
                                      [1.0000, 0.5833, 0],
                                      [1.0000, 0.6250, 0],
                                      [1.0000, 0.6667, 0],
                                      [1.0000, 0.7083, 0],
                                      [1.0000, 0.7500, 0],
                                      [1.0000, 0.7917, 0],
                                      [1.0000, 0.8333, 0],
                                      [1.0000, 0.8750, 0],
                                      [1.0000, 0.9167, 0],
                                      [1.0000, 0.9583, 0],
                                      [1.0000, 1.0000, 0],
                                      [1.0000, 1.0000, 0.0625],
                                      [1.0000, 1.0000, 0.1250],
                                      [1.0000, 1.0000, 0.1875],
                                      [1.0000, 1.0000, 0.2500],
                                      [1.0000, 1.0000, 0.3125],
                                      [1.0000, 1.0000, 0.3750],
                                      [1.0000, 1.0000, 0.4375],
                                      [1.0000, 1.0000, 0.5000],
                                      [1.0000, 1.0000, 0.5625],
                                      [1.0000, 1.0000, 0.6250],
                                      [1.0000, 1.0000, 0.6875],
                                      [1.0000, 1.0000, 0.7500],
                                      [1.0000, 1.0000, 0.8125],
                                      [1.0000, 1.0000, 0.8750],
                                      [1.0000, 1.0000, 0.9375],
                                      [1.0000, 1.0000, 1.0000]])
        self.pos = np.linspace(0, 1, len(self.mapcolors))
        self.image = pg.ImageItem(border='w')
        self.luthotmap = pg.ColorMap(self.pos, self.mapcolors)
        self.luthot = self.luthotmap.getLookupTable(0.0, 1.0, 256, True)
        self.image.setLookupTable(self.luthot)
        self.view = self.addViewBox(invertY=True, invertX=False)
        self.view.setAspectLocked(True)  # square pixels
        self.view.addItem(self.image)

    def update(self, image):
        self.image.setImage(image)


if __name__ == '__main__':

    app = QtGui.QApplication([])

    # webcam =
    win = WidefieldWidget()
    win.show()
    app.exec_()
