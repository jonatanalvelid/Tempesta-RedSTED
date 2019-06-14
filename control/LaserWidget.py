# -*- coding: utf-8 -*-

import time
from PyQt4 import QtCore
from lantz import Q_
from pyqtgraph.Qt import QtGui
import control.instruments as instruments


class LaserWidget(QtGui.QFrame):
    """Defines the layout of the whole widget including all the lasers."""
    def __init__(self, lasers, *args, **kwargs):
        """lasers: list containing the different laser objects
        """
        super().__init__(*args, **kwargs)

        self.greenlaser, self.redlaser, self.katanalaser = lasers
        self.mW = Q_(1, 'mW')

        self.greenControl = LaserControl(self.greenlaser,
                                          self.greenlaser.idn,
                                          color=(198, 255, 0), tickInterval=5,
                                          singleStep=0.1, modulable=False)
        self.redControl = LaserControl(self.redlaser,
                                          self.redlaser.idn,
                                          color=(255, 33, 0), tickInterval=5,
                                          singleStep=0.1, modulable=False)
        self.katanaControl = LaserControl(self.katanalaser,
                                          self.katanalaser.idn,
                                          color=(109, 0, 0), tickInterval=5,
                                          singleStep=0.1, modulable=False)

        self.controls = (self.greenControl, self.redControl, self.katanaControl)
#        self.controls = (self.katanaControl)

        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.greenControl, 0, 0)
        grid.addWidget(self.redControl, 0, 1)
        grid.addWidget(self.katanaControl, 0, 2)

        grid.setColumnMinimumWidth(0, 70)
        grid.setColumnMinimumWidth(1, 70)
        grid.setColumnMinimumWidth(2, 70)
        grid.setRowMinimumHeight(0,75)

        # Current power update routine
        self.updatePowers = UpdatePowers(self)
        self.updateThread = QtCore.QThread()
        self.updatePowers.moveToThread(self.updateThread)
        self.updateThread.start()
        self.updateThread.started.connect(self.updatePowers.update)

    def closeEvent(self, *args, **kwargs):
        self.updateThread.terminate()
        super().closeEvent(*args, **kwargs)


class UpdatePowers(QtCore.QObject):
    def __init__(self, laserwidget, *args, **kwargs):
        super(QtCore.QObject, self).__init__(*args, **kwargs)
        self.widget = laserwidget

    def update(self):
        greenpower = '{:~}'.format(self.widget.greenlaser.power)
        redpower = '{:~}'.format(self.widget.redlaser.power)
        katanapower = '{:~}'.format(self.widget.katanalaser.power)
        greenpower = '{:~}'.format(self.widget.greenlaser.power)
        self.widget.greenControl.powerIndicator.setText(greenpower)
        self.widget.redControl.powerIndicator.setText(redpower)
        self.widget.katanaControl.powerIndicator.setText(katanapower)
        time.sleep(1)
        QtCore.QTimer.singleShot(1, self.update)


class LaserControl(QtGui.QFrame):
    """Controls one specific laser and associates it with a specific layout: a slider and a text box to edit the
    Laser Power, and a switch on/off button."""
    def __init__(self, laser, name, color, tickInterval, singleStep, prange=None,
                 daq=None, port=None, invert=True, modulable=True, *args, **kwargs):
        """laser: instance of the laser to control
        name: string (ie 561nm Laser)
        tickInterval: int, specifies the distance between two graduations on the laser slider
        singleStep: size of the smallest increment of a laser slider"""

        super().__init__(*args, **kwargs)
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        self.laser = laser
        self.mW = Q_(1, 'mW')
#        self.daq = daq
        self.port = port
        self.laser.digital_mod = False

        self.name = QtGui.QLabel(name)
        self.name.setTextFormat(QtCore.Qt.RichText)
        self.name.setAlignment(QtCore.Qt.AlignCenter)
        self.powerIndicator = QtGui.QLineEdit('{:~}'.format(self.laser.power))
        self.powerIndicator.setReadOnly(True)
        self.powerIndicator.setFixedWidth(100)
        self.setPointEdit = QtGui.QLineEdit(str(round(self.laser.power_sp.magnitude, 3)))
        self.setPointEdit.setFixedWidth(100)
        self.enableButton = QtGui.QPushButton('ON')
        self.enableButton.setFixedWidth(100)
        style = "background-color: rgb{}".format(color)
        self.enableButton.setStyleSheet(style)
        self.enableButton.setCheckable(True)
        self.name.setStyleSheet(style)
        if self.laser.enabled:
            self.enableButton.setChecked(True)
        if(prange is None):
            prange = (0, self.laser.power.magnitude)
        self.maxpower = QtGui.QLabel(str(prange[1]))
        self.maxpower.setAlignment(QtCore.Qt.AlignCenter)
        self.slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.slider.setMinimum(prange[0])
        self.slider.setMaximum(prange[1])
        self.slider.setTickInterval(tickInterval)
        self.slider.setSingleStep(singleStep)
        self.slider.setValue(0)
        self.minpower = QtGui.QLabel(str(prange[0]))
        self.minpower.setAlignment(QtCore.Qt.AlignCenter)

        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.name, 0, 0)
        grid.addWidget(self.powerIndicator, 3, 0)
        grid.addWidget(self.setPointEdit, 4, 0)
        grid.addWidget(self.enableButton, 5, 0)
        grid.addWidget(self.maxpower, 1, 1)
        grid.addWidget(self.slider, 2, 1, 5, 1)
        grid.addWidget(self.minpower, 7, 1)
        grid.setRowMinimumHeight(2, 60)
        grid.setRowMinimumHeight(6, 60)

        # Digital modulation
        if modulable:
                self.digimodButton = QtGui.QPushButton('Digital modulation')
                style = "background-color: rgb{}".format((160, 160, 160))
                self.digimodButton.setStyleSheet(style)
                self.digimodButton.setCheckable(True)
                grid.addWidget(self.digimodButton, 6, 0)
                self.digimodButton.toggled.connect(self.digitalMod)

        # Connections
        self.enableButton.toggled.connect(self.toggleLaser)
        self.slider.valueChanged[int].connect(self.changeSlider)
        self.setPointEdit.returnPressed.connect(self.changeEdit)

    def toggleLaser(self):
        if self.enableButton.isChecked():
            self.laser.enabled = True
        else:
            self.laser.enabled = False

    def digitalMod(self):
        if self.digimodButton.isChecked():
            self.laser.digital_mod = True
            self.laser.enter_mod_mode()
            print(self.laser.mod_mode)
        else:
            self.laser.query('cp')

    def enableLaser(self):
        """Turns on the laser and sets its power to the value specified by the textbox."""
        self.laser.enabled = True
        self.laser.power_sp = float(self.setPointEdit.text()) * self.mW

    def changeSlider(self, value):
        """called when the slider is moved, sets the power of the laser to value"""
        self.laser.power_sp = self.slider.value() * self.mW
        self.setPointEdit.setText(str(round(self.laser.power_sp.magnitude*10,3)))

    def changeEdit(self):
        """called when the user manually changes the intensity value of the laser.
        Sets the laser power to the corresponding value"""
        self.laser.power_sp = float(self.setPointEdit.text()) * self.mW
        self.slider.setValue(self.laser.power_sp.magnitude)

    def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)


if __name__ == '__main__':
    app = QtGui.QApplication([])

    redlaser = instruments.Laser('cobolt.cobolt0601.Cobolt0601', 'COM12')
    katanalaser = instruments.OneFiveLaser(intensity_max=30)
    greenlaser = instruments.Laser('cobolt.cobolt0601.Cobolt0601', 'COM10')

    lasers = (redlaser, katanalaser, greenlaser)

    win = LaserWidget(lasers)
    win.show()
    app.exec_()
