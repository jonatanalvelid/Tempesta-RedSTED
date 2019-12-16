# -*- coding: utf-8 -*-

# import time
from PyQt4 import QtCore
from lantz import Q_
from pyqtgraph.Qt import QtGui
import control.instruments as instruments
import math


class LaserWidget(QtGui.QFrame):
    """Defines the layout of the whole widget including laser and aotf."""
    def __init__(self, lasers, aotf, *args, **kwargs):
        """lasers: list containing the different laser objects
        """
        super().__init__(*args, **kwargs)

        self.katanalaser = lasers
        self.aotf = aotf
#        self.mW = Q_(1, 'mW')
#        self.uW = Q_(1, 'uW')

        self.greenControl = AOTFControl(self.aotf, '561 nm Aberrior, P=max',
                                          color=(198, 255, 0), tickInterval=5,
                                          singleStep=0.1, channel=1,
                                          modulable=False)
        self.redControl = AOTFControl(self.aotf, '640 nm PicoQuant, P=3:90',
                                          color=(255, 33, 0), tickInterval=5,
                                          singleStep=0.1, channel=2,
                                          modulable=False)
        self.katanaControl = LaserControl(self.katanalaser,
                                          self.katanalaser.idn,
                                          color=(109, 0, 0), tickInterval=5,
                                          singleStep=1, modulable=False)

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

    def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)


class LaserControl(QtGui.QFrame):
    """Controls one specific laser and associates it with a specific layout:
    a slider and a text box to edit the Laser Power, and a switch on/off
    button."""
    def __init__(self, laser, name, color, tickInterval, singleStep, prange=None,
                 daq=None, port=None, invert=True, modulable=True, *args, **kwargs):
        """laser: instance of the laser to control
        name: string (ie 561nm Laser)
        tickInterval: int, specifies the distance between two graduations on
        the laser slider singleStep: size of the smallest increment of a laser
        slider"""

        super().__init__(*args, **kwargs)
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        self.laser = laser
#        self.mW = Q_(1, 'mW')
#        self.daq = daq
        self.port = port
        self.laser.digital_mod = False

        self.name = QtGui.QLabel(name)
        self.name.setTextFormat(QtCore.Qt.RichText)
        self.name.setAlignment(QtCore.Qt.AlignCenter)
        self.powerIndicator = QtGui.QLineEdit('Max: ' + str(self.laser.maxPower) + ' mW')
        self.powerIndicator.setReadOnly(True)
        self.powerIndicator.setFixedWidth(100)
        self.setPointEdit = QtGui.QLineEdit(str(round(self.laser.power_sp, 3)))
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
            prange = (0, self.laser.maxPower)
#            prange = (0, 3200)
        self.maxpower = QtGui.QLabel(str(prange[1]))
        self.maxpower.setAlignment(QtCore.Qt.AlignCenter)
        self.slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.slider.setMinimum(prange[0])
        print(prange[1])
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
        self.laser.enabled = 1
        self.laser.power_sp = int(self.setPointEdit.text())

    def changeSlider(self, value):
        """Called when the slider is moved, changes the power of the laser.
        """
        self.laser.power_sp = int(self.slider.value())
        self.setPointEdit.setText(str(self.laser.power_sp))

    def changeEdit(self):
        """called when the user manually changes the intensity value of the laser.
        Sets the laser power to the corresponding value"""
        self.laser.power_sp = int(self.setPointEdit.text())
        self.slider.setValue(self.laser.power_sp)

    def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)


class AOTFControl(QtGui.QFrame):
    """Controls one specific laser with the aotf and associates it with a
    specific layout: a slider and a text box to edit the Laser Power,
    and a switch on/off button."""
    def __init__(self, aotf, name, color, tickInterval, singleStep, channel,
                 prange=None, daq=None, port=None, invert=True, modulable=True,
                 *args, **kwargs):
        """laser: instance of the laser to control
        name: string (ie 561nm Laser)
        tickInterval: int, specifies the distance between two graduations on
        the laser slider singleStep: size of the smallest increment of a laser
        slider"""

        super().__init__(*args, **kwargs)
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        self.aotf = aotf
        self.channel = channel
        
        self.name = QtGui.QLabel(name)
        self.name.setTextFormat(QtCore.Qt.RichText)
        self.name.setAlignment(QtCore.Qt.AlignCenter)
        if channel==1:
            self.powerIndicator = QtGui.QLineEdit('Max: 21 uW')
        elif channel==2:
            self.powerIndicator = QtGui.QLineEdit('Max: 124 uW')
        self.powerIndicator.setReadOnly(True)
        self.powerIndicator.setFixedWidth(100)
        self.setPointEdit = QtGui.QLineEdit(str(0))
        self.setPointEdit.setFixedWidth(100)
        self.enableButton = QtGui.QPushButton('ON')
        self.enableButton.setFixedWidth(100)
        style = "background-color: rgb{}".format(color)
        self.enableButton.setStyleSheet(style)
        self.enableButton.setCheckable(True)
        self.name.setStyleSheet(style)
        if(prange is None):
            prange = (0, 1023)
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

        # Connections
        self.enableButton.toggled.connect(self.toggleLaser)
        self.slider.valueChanged[int].connect(self.changeSlider)
        self.setPointEdit.returnPressed.connect(self.changeEdit)

    def toggleLaser(self):
        if self.enableButton.isChecked():
            self.enableLaser()
        else:
            self.disableLaser()

    def digitalMod(self):
        if self.digimodButton.isChecked():
            self.laser.digital_mod = True
            self.laser.enter_mod_mode()
            print(self.laser.mod_mode)
        else:
            self.laser.query('cp')

    def enableLaser(self):
        """Turns on the laser, sets its power to the value specified by the textbox."""
        self.aotf.channelOn(self.channel, 1)
        self.aotf.power(self.channel, float(self.setPointEdit.text()))
        
    def disableLaser(self):
        """Turns off the laser."""
        self.aotf.channelOn(self.channel, 0)

    def changeSlider(self, value):
        """called when the slider is moved, sets the power of the laser to value"""
        self.aotf.power(self.channel, self.slider.value())
        self.setPointEdit.setText(str(round(self.slider.value())))

    def changeEdit(self):
        """called when the user manually changes the intensity value of the laser.
        Sets the laser power to the corresponding value"""
        self.aotf.power(self.channel, int(self.setPointEdit.text()))
        self.slider.setValue(float(self.setPointEdit.text()))
        
    def getOutPower(self, p_setting):
        """Get the output power in uW when given a AOTF power setting value in
        [0, 1023], valid for [0, ~920] power settings"""
        p_out = 0.08117 * math.exp(0.004165 * p_setting) + 6.563*10**(-5) * math.exp(0.01466 * p_setting)
        return float(p_out)

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
