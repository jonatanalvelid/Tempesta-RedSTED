# -*- coding: utf-8 -*-
"""
Created on Fri Sep 28 17:51:28 2018

@author: jonatan.alvelid
"""

import os
import time
import numpy as np
import pyqtgraph as pg
import scipy.ndimage as ndi
import scipy.misc as scipym
from skimage.transform import resize
from pyqtgraph.Qt import QtCore, QtGui


class WidefieldWidget(QtGui.QFrame):

    def __init__(self, webcam, main=None, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.setMinimumSize(200, 350)

        self.main = main
        self.webcam = webcam
        #self.setPoint = 0
        #self.n = 1
        self.max_dev = 0
        self.scan_freq = 15
        self.frame_time = 1000 / self.scan_freq
        self.cam_on_var = False

        # Widefield webcam graph widget
        self.webcam_graph = WebcamGraph()

        # Thread for getting the data and processing it
        self.process_data_thread = ProcessDataThread(self)
        self.process_data_thread.start()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.process_data_thread.update)
        self.timer.start(self.frame_time)

        self.cam_dialog_button = QtGui.QPushButton('Camera Dialog')
        self.cam_dialog_button.clicked.connect(self.webcam.show_dialog)
        self.snapshot_button = QtGui.QPushButton('Take snapshot')
        self.snapshot_button.clicked.connect(self.process_data_thread.take_snapshot)
        self.cam_on_box = QtGui.QCheckBox('Camera on')

        # GUI layout
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.webcam_graph, 0, 0, 4, 5)
        grid.addWidget(self.cam_dialog_button, 4, 2, 1, 5)
        grid.addWidget(self.cam_on_box, 4, 1)
        grid.addWidget(self.snapshot_button, 5, 2, 1, 5)

#        grid.setColumnMinimumWidth(1, 100)
#        grid.setColumnMinimumWidth(2, 40)
#        grid.setColumnMinimumWidth(0, 100)

        self.cam_on_box.stateChanged.connect(self.cam_on_var_change)

    def cam_on_var_change(self):
        if self.cam_on_var:
            self.cam_on_var = False
            self.timer.stop()
        else:
            self.cam_on_var = True
            self.timer.start(self.frame_time)

    def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)


class ProcessDataThread(QtCore.QThread):

    def __init__(self, widefield_widget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widefield_widget = widefield_widget
        # Set-up the camera settings
        self.webcam = self.widefield_widget.webcam
        self.ws = {'vsub': 4, 'hsub': 4,
                   'top': None, 'bot': None,
                   'exposure_time': 10}
        # Grab camera image
        self.webcam_image = self.webcam.grab_image()
        #self.sensorSize = np.array(self.webcam_image.shape)
        self.snapshotwd = r"C:\\Users\\STEDred\\Documents\\TempestaSnapshots"

    def update(self):
        if self.widefield_widget.cam_on_var:
            try:
                # then = time.time()
                self.webcam_image = self.webcam.grab_image()
                # now = time.time()
                # print("WF: Whole grab image took: ", now-then, " seconds")
                # print("")
            except:
                pass
            # imagearray = np.array(self.image)
            # imagearray = resize(imagearray, (256, 320))
            # imagearraygf = ndi.filters.gaussian_filter(imagearray, 3)  # Gaussian filter the image, to remove noise.
            self.widefield_widget.webcam_graph.update(self.webcam_image)

    def take_snapshot(self):
        if self.widefield_widget.cam_on_var:
            imagearray = np.array(self.webcam_image)
            datetimestring = time.strftime("%Y%m%d-%H%M%S")
            # filename = datetimestring + '.txi'  # .txi for text image
            filenametiff = datetimestring + '.tiff'
            # np.savetxt(filename, imagearray)
            currwd = os.getcwd()
            os.chdir(self.snapshotwd)
            scipym.toimage(imagearray, cmin=0.0, cmax=..., mode='F').save(filenametiff)
            # scipym.imsave(filenametiff, imagearray)
            os.chdir(currwd)


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

    def update(self, webcam_image):
        self.image.setImage(webcam_image)


if __name__ == '__main__':

    app = QtGui.QApplication([])

    # webcam =
    win = WidefieldWidget()
    win.show()
    app.exec_()
