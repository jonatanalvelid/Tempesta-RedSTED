# -*- coding: utf-8 -*-
"""
Created on Wed Oct 1 13:41:48 2014

@authors: Federico Barabas, Luciano Masullo, Shusei Masuda, Jonatan Alvelid
"""

import numpy as np
import time
# import threading
import scipy.ndimage as ndi
from skimage.feature import peak_local_max

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph.ptime as ptime

from lantz import Q_
import control.pi as pi
import control.instruments as instruments


class FocusWidget(QtGui.QFrame):

    def __init__(self, scanZ, webcam, imspector, main=None, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.setMinimumSize(200, 350)  # Set the minimum size of the widget

        self.main = main
        self.z = scanZ
        self.webcam = webcam
        self.imspector = imspector
        self.setPoint = 0
        self.focuspoints = np.zeros(10)
        self.calibrationResult = [0, 0]
        self.locked = False
        self.aboutToLock = False
        self.zStackVar = False
        self.twoFociVar = False
        self.n = 1
        self.max_dev = 0
        self.scansPerS = 10
        self.focusTime = 1000 / self.scansPerS
        self.zstepupdate = 0
        self.t0 = 0
        self.t1 = 0
        self.lastZ = 0
        self.currentZ = 0
        self.averageDiff = 10
        self.dataPoints = np.zeros(7)
        self.noStepVar = True
        self.countrows = 0

        self.V = Q_(1, 'V')
        self.um = Q_(1, 'um')
        self.nm = Q_(1, 'nm')

        # Focus lock widgets
        self.kpEdit = QtGui.QLineEdit('5')
        self.kpEdit.textChanged.connect(self.unlockFocus)
        self.kpLabel = QtGui.QLabel('kp')
        self.kiEdit = QtGui.QLineEdit('0.1')
        self.kiEdit.textChanged.connect(self.unlockFocus)
        self.kiLabel = QtGui.QLabel('ki')
        self.lockButton = QtGui.QPushButton('Lock')
        self.lockButton.setCheckable(True)
        self.lockButton.clicked.connect(self.toggleFocus)
        self.lockButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                      QtGui.QSizePolicy.Expanding)

        self.zStackBox = QtGui.QCheckBox('Z-stack')
        self.twoFociBox = QtGui.QCheckBox('Two foci')

        self.zStepFromLabel = QtGui.QLabel('Min step [nm]')
        self.zStepFromEdit = QtGui.QLineEdit('40')
        self.zStepToLabel = QtGui.QLabel('Max step [nm]')
        self.zStepToEdit = QtGui.QLineEdit('100')

        self.focusDataBox = QtGui.QCheckBox('Save data')
        self.camDialogButton = QtGui.QPushButton('Camera Dialog')
        self.camDialogButton.clicked.connect(self.webcam.show_dialog)

        # PZT position widgets
        self.positionLabel = QtGui.QLabel('Position[um]')
#        self.positionEdit = QtGui.QLineEdit(str(self.z.absZ).split(' ')[0])
        self.positionEdit = QtGui.QLineEdit('50')
        self.positionSetButton = QtGui.QPushButton('Set')
        self.positionSetButton.clicked.connect(self.movePZT)

        # focus calibration widgets
        self.CalibFromLabel = QtGui.QLabel('from [um]')
        self.CalibFromEdit = QtGui.QLineEdit('49')
        self.CalibToLabel = QtGui.QLabel('to [um]')
        self.CalibToEdit = QtGui.QLineEdit('51')
        self.focusCalibThread = FocusCalibThread(self)
        self.focusCalibButton = QtGui.QPushButton('Calib')
        self.focusCalibButton.setSizePolicy(QtGui.QSizePolicy.Preferred,
                                            QtGui.QSizePolicy.Expanding)
        self.focusCalibButton.clicked.connect(self.focusCalibThread.start)
        self.CalibCurveButton = QtGui.QPushButton('See Calib')
        self.CalibCurveButton.clicked.connect(self.showCalibCurve)
        self.CalibCurveWindow = CaribCurveWindow(self)
        try:
            prevCal = np.around(np.loadtxt('calibration')[0]/10)
            text = '1 px --> {} nm'.format(prevCal)
            self.calibrationDisplay = QtGui.QLineEdit(text)
        except:
            self.calibrationDisplay = QtGui.QLineEdit('0 px --> 0 nm')
        self.calibrationDisplay.setReadOnly(False)

        # focus lock graph widget
        self.focusLockGraph = FocusLockGraph(self, main)
        self.webcamGraph = WebcamGraph()

        # Thread for getting the data and processing it
        self.processDataThread = ProcessDataThread(self)
        self.processDataThread.start()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.processDataThread.update)
        self.timer.start(self.focusTime)

        # self.focusDataBox.stateChanged.connect(self.exportData)


        # GUI layout
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.focusLockGraph, 0, 0, 1, 9)
        grid.addWidget(self.webcamGraph, 0, 9, 4, 1)
        grid.addWidget(self.focusCalibButton, 1, 2, 2, 1)
        grid.addWidget(self.calibrationDisplay, 3, 0, 1, 2)
        grid.addWidget(self.kpLabel, 1, 3)
        grid.addWidget(self.kpEdit, 1, 4)
        grid.addWidget(self.kiLabel, 2, 3)
        grid.addWidget(self.kiEdit, 2, 4)
        grid.addWidget(self.lockButton, 1, 5, 2, 1)
        grid.addWidget(self.zStackBox, 4, 2)
        grid.addWidget(self.twoFociBox, 4, 6)
        grid.addWidget(self.zStepFromLabel, 3, 4)
        grid.addWidget(self.zStepFromEdit, 4, 4)
        grid.addWidget(self.zStepToLabel, 3, 5)
        grid.addWidget(self.zStepToEdit, 4, 5)
        grid.addWidget(self.focusDataBox, 4, 0, 1, 2)
        grid.addWidget(self.CalibFromLabel, 1, 0)
        grid.addWidget(self.CalibFromEdit, 1, 1)
        grid.addWidget(self.CalibToLabel, 2, 0)
        grid.addWidget(self.CalibToEdit, 2, 1)
        grid.addWidget(self.CalibCurveButton, 3, 2)
        grid.addWidget(self.positionLabel, 1, 6)
        grid.addWidget(self.positionEdit, 1, 7)
        grid.addWidget(self.positionSetButton, 2, 6, 1, 2)
        grid.addWidget(self.camDialogButton, 3, 6, 1, 2)

#        grid.setColumnMinimumWidth(1, 100)
#        grid.setColumnMinimumWidth(2, 40)
#        grid.setColumnMinimumWidth(0, 100)

        self.zStackBox.stateChanged.connect(self.zStackVarChange)
        self.twoFociBox.stateChanged.connect(self.twoFociVarChange)

    def __call__(self):
        self.countrows = self.countrows + 1
        if self.countrows == self.rowsperframe:
            self.countrows = 0
            self.unlockFocus()
            self.ZStep()
            # slice is finished, move to next plane in a good way!
            
    def movePZT(self):
        self.z.move_absZ(float(self.positionEdit.text()) * self.um)

    def toggleFocus(self):
        self.aboutToLock = False
        if self.lockButton.isChecked():
            self.lockFocusFirst()
            self.lockButton.setText('Unlock')
        else:
            self.unlockFocus()
            self.lockButton.setText('Lock')

    def zStackVarChange(self):
        if self.zStackVar:
            # Do all the things needed to be done when you finish end a z-stack
            self.zStackVar = False
            self.imspector.disconnect_end(self,1)
        else:
            # Do all the things needed to be done when you start end a z-stack
            self.zStackVar = True
            self.countrows = 0
            
            self.immeasurement = self.imspector.active_measurement()
            self.measurementparams = self.immeasurement.parameters('')

            if self.measurementparams['Measurement']['ThdAxis'] == 'NiDAQ6353 DACs::Z':
                print('One-color z-stack in progress!')
                self.imspector.connect_end(self,1)
                self.rowsperframe = self.measurementparams['NiDAQ6353'][':YRes']
                print(self.rowsperframe)
            elif self.measurementparams['Measurement']['FthAxis'] == 'NiDAQ6353 DACs::Z':
                print('Two-color z-stack in progress!')
                self.imspector.connect_end(self,1)
                # Use double the number of rows, as we are doing two-color imaging, and as such want to take the next tile when we have scanned 2*the whole frame
                self.rowsperframe = 2*self.measurementparams['NiDAQ6353'][':YRes']
                print(self.rowsperframe)
            else:
                print('Axises in Imspector are not properly set-up for a z-stack. Double check you settings.')
                return

    def twoFociVarChange(self):
        if self.twoFociVar:
            self.twoFociVar = False
        else:
            self.twoFociVar = True

    def lockFocus(self):
        if not self.locked:
            self.lockingpoints = np.sort(self.dataPoints)
            self.lockingpoints = np.delete(self.lockingpoints, 0)
            self.lockingpoints = np.delete(self.lockingpoints, -1)
            self.setPoint = np.mean(self.lockingpoints)
            self.focusLockGraph.line = self.focusLockGraph.plot.addLine(
                                                    y=self.setPoint, pen='r')
            self.PI = pi.PI(self.setPoint, 0.001,
                            np.float(self.kpEdit.text()),
                            np.float(self.kiEdit.text()))
            self.initialZ = self.z.absZ
            self.locked = True
            self.stepDistLow = 0.001 * np.float(self.zStepFromEdit.text())
            self.stepDistHigh = 0.001 * np.float(self.zStepToEdit.text())
            #print(self.stepDistance)
            print('%.2f s' % self.zsteptime)
            print(' ')

    def lockFocusFirst(self):
        if not self.locked:
            self.setPoint = self.processDataThread.focusSignal
            self.focusLockGraph.line = self.focusLockGraph.plot.addLine(
                                                    y=self.setPoint, pen='r')
            self.PI = pi.PI(self.setPoint, 0.001,
                            np.float(self.kpEdit.text()),
                            np.float(self.kiEdit.text()))
            self.initialZ = self.z.absZ
            self.locked = True
            self.stepDistLow = 0.001 * np.float(self.zStepFromEdit.text())
            self.stepDistHigh = 0.001 * np.float(self.zStepToEdit.text())

    def lockFocusSetPos(self, newFocusPos):
        if not self.locked:
            self.setPoint = newFocusPos
            self.focusLockGraph.line = self.focusLockGraph.plot.addLine(
                                                    y=self.setPoint, pen='r')
            self.PI = pi.PI(self.setPoint, 0.001,
                            np.float(self.kpEdit.text()),
                            np.float(self.kiEdit.text()))
            self.initialZ = self.z.absZ
            self.locked = True
            self.stepDistLow = 0.001 * np.float(self.zStepFromEdit.text())
            self.stepDistHigh = 0.001 * np.float(self.zStepToEdit.text())
            
    def unlockFocus(self):
        if self.locked:
            self.locked = False
            self.lockButton.setChecked(False)
            self.focusLockGraph.plot.removeItem(self.focusLockGraph.line)

    def updatePI(self):
        if not self.noStepVar:
            self.noStepVar = True
        self.currentZ = self.z.absZ
        self.distance = self.currentZ - self.initialZ
        self.stepDistance = self.currentZ - self.lastZ
        out = self.PI.update(self.processDataThread.focusSignal)
        self.lastZ = self.currentZ

        if abs(self.distance) > 5 * self.um or abs(out) > 3:
            print('Safety unlocking!')
            self.unlockFocus()
#        elif self.zStackVar and self.zstepupdate > 15:
#            if self.stepDistance > self.stepDistLow * self.um and self.stepDistance < self.stepDistHigh * self.um:
#                self.unlockFocus()
#                self.dataPoints = np.zeros(5)
#                self.averageDiff = 10
#                self.aboutToLock = True
#                self.t0 = time.time()
#                self.zsteptime = self.t0-self.t1
#                self.t1 = self.t0
#                self.noStepVar = False
        if self.noStepVar and abs(out) > 0.002:
            self.zstepupdate = self.zstepupdate + 1
            self.z.move_relZ(out * self.um)

    def lockingPI(self):
        self.dataPoints[:-1] = self.dataPoints[1:]
        self.dataPoints[-1] = self.processDataThread.focusSignal
        self.averageDiff = np.std(self.dataPoints)
        if self.averageDiff < 0.4:
            self.lockFocus()
            self.aboutToLock = False

    def tilingStep(self, newFocusPos=False):
        # Call this function whenever there is a tiling step taken. Lock the focus in a new position.
        # Do it at a sensed new position, as a z-step, if not newFocusPos is given as the new focal position.
        if not newFocusPos:
            self.dataPoints = np.zeros(5)
            self.averageDiff = 10
            self.aboutToLock = True
        else:
            self.lockFocusSetPos(newFocusPos)

    def ZStep(self, newFocusPos=False):
        # Call this function whenever there is a z-stack step about to be taken. Lock the focus in a new position.
        # Do it at a sensed new position, as a z-step. 
        self.dataPoints = np.zeros(5)
        self.averageDiff = 10
        self.aboutToLock = True
        self.t0 = time.time()
        self.zsteptime = self.t0-self.t1
        self.t1 = self.t0
        self.noStepVar = False
            
    def getFocusPosition(self):
        # Return the current focus locked spot position
        return self.setPoint

    def exportData(self):
        self.sizeofData = np.size(self.graph.savedDataSignal)
        self.savedData = np.transpose([self.graph.savedDataTime,
                    self.graph.savedDataSignal, np.ones(self.sizeofData)*self.setPoint])
        np.savetxt('focusreaddata.txt', self.savedData)

        # self.sizeofCData = np.size(self.savedCommandsData)
        # self.savedCData = np.transpose([self.savedCommandsTime, self.savedCommandsData])
        # print(np.transpose([self.savedCommandsData, self.savedCommandsTime]))
        # np.savetxt('focuscommandsdata.txt', self.savedCData)

        self.graph.savedDataSignal = []
        self.graph.savedDataTime = []
        # self.savedCommandsData = []
        # self.savedCommandsTime = []

    def analizeFocus(self):
        if self.n == 1:
            self.mean = self.processDataThread.focusSignal
            self.mean2 = self.processDataThread.focusSignal**2
        else:
            self.mean += (self.processDataThread.focusSignal -
                          self.mean)/self.n
            self.mean2 += (self.processDataThread.focusSignal**2 -
                           self.mean2)/self.n

        self.std = np.sqrt(self.mean2 - self.mean**2)

        self.max_dev = np.max([self.max_dev,
                              self.processDataThread.focusSignal -
                              self.setPoint])

        statData = 'std = {}    max_dev = {}'.format(np.round(self.std, 3),
                                                     np.round(self.max_dev, 3))
        self.focusLockGraph.statistics.setText(statData)

        self.n += 1

    def showCalibCurve(self):
        self.CalibCurveWindow.run()
        self.CalibCurveWindow.show()

    def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)


class ProcessDataThread(QtCore.QThread):

    def __init__(self, focusWidget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.focusWidget = focusWidget
        # set the camera
        """
        uc480 camera

        default exposureTime: 10 ms
                vsub: 1024 pix
                hsub: 1280 pix
                exp. time *u.ms
        """
        self.webcam = self.focusWidget.webcam
        self.ws = {'vsub': 4, 'hsub': 4,
                   'top': None, 'bot': None,
                   'exposure_time': 10}
        # self.image = self.webcam.grab_image(vsub=self.ws['vsub'],
        #                                     hsub=self.ws['hsub'],
        #                                     top=self.ws['top'],
        #                                     bot=self.ws['bot'],
        #                                     exposure_time=self.ws[
        #                                     'exposure_time'])
        self.image = self.webcam.grab_image()

        self.sensorSize = np.array(self.image.shape)
        # print(self.sensorSize) #= (1024,1280)

        self.focusSignal = 0

    def update(self):
        self.updateFS()
        self.focusWidget.webcamGraph.update(self.image)
        self.focusWidget.focusLockGraph.update(self.focusSignal)
        # update the PI control
        if self.focusWidget.locked:
            self.focusWidget.updatePI()
        elif self.focusWidget.aboutToLock:
            self.focusWidget.lockingPI()

    def updateFS(self):
        # update the focus signal
        # print('Updating focus signal...')
        try:
            # self.image = self.webcam.grab_image(vsub=self.ws['vsub'],
            #                                     hsub=self.ws['hsub'],
            #                                     top=self.ws['top'],
            #                                     bot=self.ws['bot'])
#            then = time.time()
            self.image = self.webcam.grab_image()
#            now = time.time()
#            print("Focus: Whole grab image took:", now-then, "seconds.")
            # print("")
        except:
            print("No image grabbed.")
            pass
        imagearray = self.image
#        imagearray = imagearray[0:720,200:1310]
#        imagearray = imagearray[300:450,0:1310]
#        print(np.size(imagearray))
#        print(np.shape(imagearray))
        imagearray = imagearray[0:1024,730:830]
        imagearray = np.swapaxes(imagearray,0,1)      # Swap matrix axes, after having turned the camera 90deg
        # imagearraygf = imagearray
        imagearraygf = ndi.filters.gaussian_filter(imagearray,7)     # Gaussian filter the image, to remove noise and so on, to get a better center estimate

        if self.focusWidget.twoFociVar:
            allmaxcoords = peak_local_max(imagearraygf, min_distance=60)
#            print(allmaxcoords)
            size = allmaxcoords.shape
            maxvals = np.zeros(size[0])
            maxvalpos = np.zeros(2)
            for n in range(0,size[0]):
                if imagearraygf[allmaxcoords[n][0],allmaxcoords[n][1]] > maxvals[0]:
                    if imagearraygf[allmaxcoords[n][0],allmaxcoords[n][1]] > maxvals[1]:
                        tempval = maxvals[1]
                        maxvals[0] = tempval
                        maxvals[1] = imagearraygf[allmaxcoords[n][0],allmaxcoords[n][1]]
                        tempval = maxvalpos[1]
                        maxvalpos[0] = tempval
                        maxvalpos[1] = n
                    else:
                        maxvals[0] = imagearraygf[allmaxcoords[n][0],allmaxcoords[n][1]]
                        maxvalpos[0] = n
            xcenter = allmaxcoords[maxvalpos[0]][0]
            ycenter = allmaxcoords[maxvalpos[0]][1]
            if allmaxcoords[maxvalpos[1]][1] < ycenter:
                xcenter = allmaxcoords[maxvalpos[1]][0]
                ycenter = allmaxcoords[maxvalpos[1]][1]
            centercoords2 = np.array([xcenter,ycenter])
        else:
            centercoords = np.where(imagearraygf == np.array(imagearraygf.max()))
            centercoords2 = np.array([centercoords[0][0],centercoords[1][0]])
            
        subsizey = 50
        subsizex = 50
        xlow = max(0,(centercoords2[0]-subsizex))
        xhigh = min(1024,(centercoords2[0]+subsizex))
        ylow = max(0,(centercoords2[1]-subsizey))
        yhigh = min(1280,(centercoords2[1]+subsizey))
        #print(xlow)
        #print(xhigh)
        #print(ylow)
        #print(yhigh)
        imagearraygfsub = imagearraygf[xlow:xhigh,ylow:yhigh]
        #imagearraygfsub = imagearraygf[xlow:xhigh,:]
        #imagearraygfsubtest = imagearraygf
        #zeroindices = np.zeros(imagearray.shape)
        #zeroindices[xlow:xhigh,ylow:yhigh] = 1
        #imagearraygfsubtest = np.multiply(imagearraygfsubtest,zeroindices)
        self.image = imagearraygf
        #print(centercoords2[1])
        self.massCenter = np.array(ndi.measurements.center_of_mass(imagearraygfsub))
        #self.massCenter2 = np.array(ndi.measurements.center_of_mass(imagearraygfsubtest))
        # self.massCenterGlobal[0] = self.massCenter[0] #+ centercoords2[0] #- subsizex - self.sensorSize[0] / 2     #add the information about where the center of the subarray is
        self.massCenterGlobal = self.massCenter[1] + centercoords2[1] #- subsizey - self.sensorSize[1] / 2     #add the information about where the center of the subarray is
#        print(self.massCenter[1])
#        print(self.massCenterGlobal)
#        print(centercoords2[1])
#        print('')
        #print(self.massCenter2[1])
        #print('')
        self.focusSignal = self.massCenterGlobal
        
#        # Try to add-project (or max intensity maybe is better?) the matrix
#        # onto the yaxis, and see if the focus lock becomes more robust
##        imagearraygfsub = imagearraygf[xlow:xhigh,ylow:yhigh]
#        imagearraygfsub = imagearraygf
#        self.image = imagearraygf
#        imagearraygfsubproj = imagearraygfsub.sum(axis=0)
#        print(imagearraygfsubproj.shape)
#        #print(centercoords2[1])
#        self.massCenter = np.array(ndi.measurements.center_of_mass(imagearraygfsubproj))
#        #self.massCenter2 = np.array(ndi.measurements.center_of_mass(imagearraygfsubtest))
##        print('hey')
#        self.massCenterGlobal = 0
#        self.massCenterGlobal = self.massCenter #+ centercoords2[1] #- subsizey - self.sensorSize[1] / 2     #add the information about where the center of the subarray is
#        print(self.massCenter)
#        print(self.massCenterGlobal)
#        print(centercoords2[1])
#        print('')
#        #print(self.massCenter2[1])
#        #print('')
#        self.focusSignal = self.massCenterGlobal


class FocusLockGraph(pg.GraphicsWindow):

    def __init__(self, focusWidget, main=None, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.focusWidget = focusWidget
        self.main = main
        self.analize = self.focusWidget.analizeFocus
        self.focusDataBox = self.focusWidget.focusDataBox
        self.savedDataSignal = []
        self.savedDataTime = []
        self.savedDataPosition = []

        self.setWindowTitle('Focus')
        self.setAntialiasing(True)

        self.npoints = 40
        self.data = np.zeros(self.npoints)
        self.ptr = 0

        # Graph without a fixed range
        self.statistics = pg.LabelItem(justify='right')
        self.addItem(self.statistics)
        self.statistics.setText('---')
        self.plot = self.addPlot(row=1, col=0)
        self.plot.setLabels(bottom=('Time', 's'),
                            left=('Laser position', 'px'))
        self.plot.showGrid(x=True, y=True)
        self.focusCurve = self.plot.plot(pen='y')

        self.time = np.zeros(self.npoints)
        self.startTime = ptime.time()

        if self.main is not None:
            self.recButton = self.main.recButton

    def update(self, focusSignal):
        """ Update the data displayed in the graphs"""
        self.focusSignal = focusSignal

        if self.ptr < self.npoints:
            self.data[self.ptr] = self.focusSignal
            self.time[self.ptr] = ptime.time() - self.startTime
            self.focusCurve.setData(self.time[1:self.ptr + 1],
                                    self.data[1:self.ptr + 1])

        else:
            self.data[:-1] = self.data[1:]
            self.data[-1] = self.focusSignal
            self.time[:-1] = self.time[1:]
            self.time[-1] = ptime.time() - self.startTime

            self.focusCurve.setData(self.time, self.data)

        self.ptr += 1

        #if self.main is not None:
        #    if self.focusDataBox.isChecked():
        #        print("saving data")
        #        self.savedDataSignal.append(self.focusSignal)
        #        self.savedDataTime.append(self.time[-1])
        #        self.analize()

    def dumpData(self):
        return self.data


class WebcamGraph(pg.GraphicsWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image = pg.ImageItem(border='w')
        self.view = self.addViewBox(invertY=True, invertX=False)
        self.view.setAspectLocked(True)  # square pixels
        self.view.addItem(self.image)

    def update(self, image):
        self.image.setImage(image)


class FocusCalibThread(QtCore.QThread):

    def __init__(self, focusWidget, *args, **kwargs):

        super().__init__(*args, **kwargs)

#        self.stream = mainwidget.stream
        self.z = focusWidget.z
        self.focusWidget = focusWidget  # mainwidget será FocusLockWidget
        self.um = Q_(1, 'micrometer')

    def run(self):
        self.signalData = []
        self.positionData = []
        self.start = np.float(self.focusWidget.CalibFromEdit.text())
        self.end = np.float(self.focusWidget.CalibToEdit.text())
        self.scan_list = np.round(np.linspace(self.start, self.end, 20), 2)
        for x in self.scan_list:
            self.z.move_absZ(x * self.um)
            time.sleep(0.5)
            self.focusCalibSignal = \
                self.focusWidget.processDataThread.focusSignal
            self.signalData.append(self.focusCalibSignal)
            self.positionData.append(self.z.absZ.magnitude)

        self.poly = np.polyfit(self.positionData, self.signalData, 1)
        self.calibrationResult = np.around(self.poly, 4)
        self.export()

    def export(self):

        np.savetxt('calibration.txt', self.calibrationResult)
        cal = self.poly[0]
        calText = '1 px --> {} nm'.format(np.round(1000/cal, 1))
        self.focusWidget.calibrationDisplay.setText(calText)
        d = [self.positionData, self.calibrationResult[::-1]]
        self.savedCalibData = [self.positionData,
                               self.signalData,
                               np.polynomial.polynomial.polyval(d[0], d[1])]
        np.savetxt('calibrationcurves.txt', self.savedCalibData)


class CaribCurveWindow(QtGui.QFrame):
    def __init__(self, focusWidget):
        super().__init__()
        self.main = focusWidget
        self.FocusCalibGraph = FocusCalibGraph(focusWidget)
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.FocusCalibGraph, 0, 0)

    def run(self):
        self.FocusCalibGraph.draw()


class FocusCalibGraph(pg.GraphicsWindow):

    def __init__(self, focusWidget, main=None, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.focusWidget = focusWidget

        # Graph without a fixed range
        self.plot = self.addPlot(row=1, col=0)
        self.plot.setLabels(bottom=('Piezo position', 'um'),
                            left=('Laser position', 'px'))
        self.plot.showGrid(x=True, y=True)

    def draw(self):
        self.plot.clear()
        self.signalData = self.focusWidget.focusCalibThread.signalData
        self.positionData = self.focusWidget.focusCalibThread.positionData
        self.poly = self.focusWidget.focusCalibThread.poly
        self.plot.plot(self.positionData,
                       self.signalData, pen=None, symbol='o')
        self.plot.plot(self.positionData,
                       np.polyval(self.poly, self.positionData), pen='r')

if __name__ == '__main__':

    app = QtGui.QApplication([])

    with instruments.PCZPiezo('COM14') as z:
        win = FocusWidget(z)
        win.show()
        app.exec_()
