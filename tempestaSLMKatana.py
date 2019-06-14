# -*- coding: utf-8 -*-
"""
Created on Mon Jan 23 15:20:04 2017

@author: STEDred
"""

from pyqtgraph.Qt import QtGui

def main():

    from control import control
    import control.instruments as instruments

    app = QtGui.QApplication([])

#TO DO: create an instruments.Camera(hamamatsu) or something similar

#    with instruments.Camera('hamamatsu.hamamatsu_camera.HamamatsuCameraMR') as orcaflash, \
    with instruments.Laser('cobolt.cobolt0601.Cobolt0601', 'COM11') as greenlaser, \
         instruments.Laser('cobolt.cobolt0601.Cobolt0601', 'COM10') as redlaser, \
         instruments.OneFiveLaser(intensity_max=30) as katanalaser, \
         instruments.SLM() as slm, \
         instruments.ScanZ('COM19') as scanZ, \
         instruments.XYStage('COM20') as scanXY:
         # sp.Imspector() as imspector:

        print(katanalaser.idn)
        print(scanZ.idn)
        print(scanXY.idn)
        # print(imspector.version())

        webcamFocusLock = instruments.CameraTIS(0, 0, 0, 0)
        webcamWidefield = instruments.CameraTIS(1, 25, 17, 725)

        win = control.TempestaSLMKatanaGUI(greenlaser, redlaser, katanalaser,
                                           slm, scanZ, scanXY, webcamFocusLock,
                                           webcamWidefield)
        win.show()
        app.exec_()

def analysisApp():

    from analysis import analysis

    app = QtGui.QApplication([])

    win = analysis.AnalysisWidget()
    win.show()

    app.exec_()

