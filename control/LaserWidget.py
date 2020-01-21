# -*- coding: utf-8 -*-
"""
Created on Mon Jan 23 15:21:07 2017

@author: STEDred, jonatanalvelid, aurelien.barbotin
"""

# import time
import math
from PyQt4 import QtCore
#from lantz import Q_
from pyqtgraph.Qt import QtGui


class LaserWidget(QtGui.QFrame):
    """Defines the layout of the whole widget including laser and aotf."""
    def __init__(self, katanalaser, aotf, *args, **kwargs):
        """katanalaser: list containing the different laser objects
        """
        super().__init__(*args, **kwargs)

        self.katanalaser = katanalaser
        self.aotf = aotf
#        self.mW = Q_(1, 'mW')
#        self.uW = Q_(1, 'uW')

        self.green_control = AOTFControl(self.aotf, '561 nm Aberrior, P=max',
                                         color=(198, 255, 0), tick_interval=5,
                                         single_step=0.1, channel=1)
        self.red_control = AOTFControl(self.aotf, '640 nm PicoQuant, P=3:90',
                                       color=(255, 33, 0), tick_interval=5,
                                       single_step=0.1, channel=2)
        self.katana_control = LaserControl(self.katanalaser, self.katanalaser.idn,
                                           color=(109, 0, 0), tick_interval=5,
                                           single_step=1)

        self.controls = (self.green_control, self.red_control, self.katana_control)
#        self.controls = (self.katanaControl)

        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.green_control, 0, 0)
        grid.addWidget(self.red_control, 0, 1)
        grid.addWidget(self.katana_control, 0, 2)

        grid.setColumnMinimumWidth(0, 70)
        grid.setColumnMinimumWidth(1, 70)
        grid.setColumnMinimumWidth(2, 70)
        grid.setRowMinimumHeight(0, 75)

    def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)


class LaserControl(QtGui.QFrame):
    """Controls one specific laser and associates it with a specific layout:
    a slider and a text box to edit the Laser Power, and a switch on/off
    button."""

    # pylint: disable=too-many-locals, too-many-arguments, keyword-arg-before-vararg, too-many-instance-attributes
    # More is reasonable in this case.

    def __init__(self, laser, name, color, tick_interval, single_step, prange=None,
                 *args, **kwargs):
        """laser: instance of the laser to control
        name: string (ie 561nm Laser)
        tickInterval: int, specifies the distance between two graduations on
        the laser slider single_step: size of the smallest increment of a laser
        slider"""

        super().__init__(*args, **kwargs)
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        self.laser = laser
        self.laser.digital_mod = False

        self.name = QtGui.QLabel(name)
        self.name.setTextFormat(QtCore.Qt.RichText)
        self.name.setAlignment(QtCore.Qt.AlignCenter)
        self.power_indicator = QtGui.QLineEdit('Max: ' + str(self.laser.maxPower) + ' mW')
        self.power_indicator.setReadOnly(True)
        self.power_indicator.setFixedWidth(100)
        self.set_point_edit = QtGui.QLineEdit(str(round(self.laser.power_sp, 3)))
        self.set_point_edit.setFixedWidth(100)
        self.enable_button = QtGui.QPushButton('ON')
        self.enable_button.setFixedWidth(100)
        style = "background-color: rgb{}".format(color)
        self.enable_button.setStyleSheet(style)
        self.enable_button.setCheckable(True)
        self.name.setStyleSheet(style)
        if self.laser.enabled:
            self.enable_button.setChecked(True)
        if prange is None:
            prange = (0, self.laser.maxPower)
        self.maxpower = QtGui.QLabel(str(prange[1]))
        self.maxpower.setAlignment(QtCore.Qt.AlignCenter)
        self.slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.slider.setMinimum(prange[0])
        print(prange[1])
        self.slider.setMaximum(prange[1])
        self.slider.setTickInterval(tick_interval)
        self.slider.setSingleStep(single_step)
        self.slider.setValue(0)
        self.minpower = QtGui.QLabel(str(prange[0]))
        self.minpower.setAlignment(QtCore.Qt.AlignCenter)

        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.name, 0, 0)
        grid.addWidget(self.power_indicator, 3, 0)
        grid.addWidget(self.set_point_edit, 4, 0)
        grid.addWidget(self.enable_button, 5, 0)
        grid.addWidget(self.maxpower, 1, 1)
        grid.addWidget(self.slider, 2, 1, 5, 1)
        grid.addWidget(self.minpower, 7, 1)
        grid.setRowMinimumHeight(2, 60)
        grid.setRowMinimumHeight(6, 60)

        # Connections
        self.enable_button.toggled.connect(self.toggle_laser)
        self.slider.valueChanged[int].connect(self.change_slider)
        self.set_point_edit.returnPressed.connect(self.change_edit)

    def toggle_laser(self):
        """Turns on/off the laser."""
        if self.enable_button.isChecked():
            self.laser.enabled = True
        else:
            self.laser.enabled = False

    def enable_laser(self):
        """Turns on the laser and sets its power to the value specified by the textbox."""
        self.laser.enabled = 1
        self.laser.power_sp = int(self.set_point_edit.text())

    def change_slider(self):
        """Called when the slider is moved, changes the power of the laser.
        """
        self.laser.power_sp = int(self.slider.value())
        self.set_point_edit.setText(str(self.laser.power_sp))

    def change_edit(self):
        """called when the user manually changes the intensity value of the laser.
        Sets the laser power to the corresponding value"""
        self.laser.power_sp = int(self.set_point_edit.text())
        self.slider.setValue(self.laser.power_sp)

    def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)


class AOTFControl(QtGui.QFrame):
    """Controls one specific laser with the aotf and associates it with a
    specific layout: a slider and a text box to edit the Laser Power,
    and a switch on/off button."""

    # pylint: disable=too-many-instance-attributes, keyword-arg-before-vararg, too-many-arguments
    # More is reasonable in this case.

    def __init__(self, aotf, name, color, tick_interval, single_step, channel, prange=None,
                 *args, **kwargs):
        """laser: instance of the laser to control
        name: string (ie 561nm Laser)
        tick_interval: int, specifies the distance between two graduations on
        the laser slider single_step: size of the smallest increment of a laser
        slider"""

        super().__init__(*args, **kwargs)
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        self.aotf = aotf
        self.channel = channel
        
        self.name = QtGui.QLabel(name)
        self.name.setTextFormat(QtCore.Qt.RichText)
        self.name.setAlignment(QtCore.Qt.AlignCenter)
        if channel == 1:
            self.power_indicator = QtGui.QLineEdit('Max: 21 uW')
        elif channel == 2:
            self.power_indicator = QtGui.QLineEdit('Max: 124 uW')
        self.power_indicator.setReadOnly(True)
        self.power_indicator.setFixedWidth(100)
        self.set_point_edit = QtGui.QLineEdit(str(0))
        self.set_point_edit.setFixedWidth(100)
        self.enable_button = QtGui.QPushButton('ON')
        self.enable_button.setFixedWidth(100)
        style = "background-color: rgb{}".format(color)
        self.enable_button.setStyleSheet(style)
        self.enable_button.setCheckable(True)
        self.name.setStyleSheet(style)
        if(prange is None):
            prange = (0, 1023)
        self.maxpower = QtGui.QLabel(str(prange[1]))
        self.maxpower.setAlignment(QtCore.Qt.AlignCenter)
        self.slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.slider.setMinimum(prange[0])
        self.slider.setMaximum(prange[1])
        self.slider.setTickInterval(tick_interval)
        self.slider.setSingleStep(single_step)
        self.slider.setValue(0)
        self.minpower = QtGui.QLabel(str(prange[0]))
        self.minpower.setAlignment(QtCore.Qt.AlignCenter)

        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.name, 0, 0)
        grid.addWidget(self.power_indicator, 3, 0)
        grid.addWidget(self.set_point_edit, 4, 0)
        grid.addWidget(self.enable_button, 5, 0)
        grid.addWidget(self.maxpower, 1, 1)
        grid.addWidget(self.slider, 2, 1, 5, 1)
        grid.addWidget(self.minpower, 7, 1)
        grid.setRowMinimumHeight(2, 60)
        grid.setRowMinimumHeight(6, 60)

        # Connections
        self.enable_button.toggled.connect(self.toggle_laser)
        self.slider.valueChanged[int].connect(self.change_slider)
        self.set_point_edit.returnPressed.connect(self.change_edit)

    def toggle_laser(self):
        if self.enable_button.isChecked():
            self.enable_laser()
        else:
            self.enable_laser()

    def enable_laser(self):
        """Turns on the laser, sets its power to the value specified by the textbox."""
        self.aotf.channelOn(self.channel, 1)
        self.aotf.power(self.channel, float(self.set_point_edit.text()))
        
    def disable_laser(self):
        """Turns off the laser."""
        self.aotf.channelOn(self.channel, 0)

    def change_slider(self):
        """called when the slider is moved, sets the power of the laser to value"""
        self.aotf.power(self.channel, self.slider.value())
        self.set_point_edit.setText(str(round(self.slider.value())))

    def change_edit(self):
        """called when the user manually changes the intensity value of the laser.
        Sets the laser power to the corresponding value"""
        self.aotf.power(self.channel, int(self.set_point_edit.text()))
        self.slider.setValue(float(self.set_point_edit.text()))
        
    def get_out_power(self, p_setting):
        """Get the output power in uW when given a AOTF power setting value in
        [0, 1023], valid for [0, ~920] power settings"""
        p_out = 0.08117 * math.exp(0.004165 * p_setting) + 6.563*10**(-5) * math.exp(0.01466 * p_setting)
        return float(p_out)

    def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)
