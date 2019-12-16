# -*- coding: utf-8 -*-
"""
Created on Mon Dec 16 15:48:00 2019

Widget for controlling the Leica objective motorized correction collar.

@author: jonatanalvelid
"""

from pyqtgraph.Qt import QtGui
from PyQt4 import QtCore


# communication with Imspector.
class MotcorrWidget(QtGui.QFrame):

    def __init__(self, dmi8, main=None, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.setMinimumSize(200, 100)  # Set the minimum size of the widget

        self.dmi8 = dmi8
        self.main = main
        self.motcorrpos = 0  # Current motorized correction collar position

        self.motcorrControl = MotcorrControl(self.dmi8, 'Glycerol motCorr [%]',
                                          color=(255, 255, 255), tickInterval=5,
                                          singleStep=0.1, modulable=False)

        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.motcorrControl, 0, 0)

        grid.setColumnMinimumWidth(0, 70)
        grid.setRowMinimumHeight(0,75)


    def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)


if __name__ == '__main__':

    app = QtGui.QApplication([])

    win = MotcorrWidget()
    win.show()
    app.exec_()


class MotcorrControl(QtGui.QFrame):
    """Controls one specific laser with the aotf and associates it with a
    specific layout: a slider and a text box to edit the Laser Power,
    and a switch on/off button."""
    def __init__(self, dmi8, name, color, tickInterval, singleStep,
                 prange=None, daq=None, port=None, invert=True, modulable=True,
                 *args, **kwargs):
        """laser: instance of the laser to control
        name: string (ie 561nm Laser)
        tickInterval: int, specifies the distance between two graduations on
        the laser slider singleStep: size of the smallest increment of a laser
        slider"""

        super().__init__(*args, **kwargs)
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Raised)
        self.dmi8 = dmi8
        
        self.name = QtGui.QLabel(name)
        self.name.setTextFormat(QtCore.Qt.RichText)
        self.name.setAlignment(QtCore.Qt.AlignCenter)
        self.powerIndicator = QtGui.QLineEdit('Max: 100%')
        self.powerIndicator.setReadOnly(True)
        self.powerIndicator.setFixedWidth(100)
        self.setPointEdit = QtGui.QLineEdit(str(0))
        self.setPointEdit.setFixedWidth(100)
        if(prange is None):
            prange = (0, 100)
        self.maxpower = QtGui.QLabel(str(prange[1]))
        self.maxpower.setAlignment(QtCore.Qt.AlignCenter)
        self.slider = QtGui.QSlider(QtCore.Qt.Vertical, self)
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.slider.setMinimum(prange[0])
        self.slider.setMaximum(prange[1])
        self.slider.setTickInterval(tickInterval)
        self.slider.setSingleStep(singleStep)
        self.slider.setValue(50)
        self.minpower = QtGui.QLabel(str(prange[0]))
        self.minpower.setAlignment(QtCore.Qt.AlignCenter)

        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.name, 0, 0)
        grid.addWidget(self.powerIndicator, 3, 0)
        grid.addWidget(self.setPointEdit, 4, 0)
        grid.addWidget(self.maxpower, 1, 1)
        grid.addWidget(self.slider, 2, 1, 5, 1)
        grid.addWidget(self.minpower, 7, 1)
        grid.setRowMinimumHeight(2, 60)
        grid.setRowMinimumHeight(6, 60)

        # Connections
#        self.slider.sliderPressed.connect(self.sldDisconnect)
#        self.slider.sliderReleased.connect(self.sldReconnect)
        self.slider.valueChanged[int].connect(self.changeSlider)
        self.setPointEdit.returnPressed.connect(self.changeEdit)
        

#    def sldDisconnect(self, value):
#        """This and the below function are made in order to only send the
#        changed value once when changing the slider."""
#        self.sender().valueChanged.disconnect()
#
#    def sldReconnect(self, value):
#        """This and the above function are made in order to only send the
#        changed value once when changing the slider."""
#        self.sender().valueChanged[int].connect(self.changeSlider)
#        self.sender().valueChanged.emit(self.sender().value())

    def changeSlider(self, value):
        """called when the slider is moved, sets the power of the laser to
        value."""
        self.dmi8.motCorrPos(self.slider.value())
        self.setPointEdit.setText(str(self.slider.value()))

    def changeEdit(self):
        """called when the user manually changes the intensity value of the
        laser. Sets the laser power to the corresponding value."""
        self.dmi8.motCorrPos(float(self.setPointEdit.text()))
        self.slider.setValue(float(self.setPointEdit.text()))


    def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)

