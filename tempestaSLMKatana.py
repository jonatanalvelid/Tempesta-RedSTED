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
#    with instruments.OneFiveLaser(intensity_max=30) as katanalaser, \
#         instruments.SLM() as slm, \
#         instruments.ScanZ('COM19') as scanZ, \
#         instruments.XYStage('COM20') as scanXY, \
#         instruments.AOTF('COM18') as aotf:

    katanalaser = instruments.OneFiveLaser(intensity_max=30)
    scanZ = instruments.ScanZ('COM19')
    scanXY = instruments.XYStage('COM20')
    aotf = instruments.AOTF('COM18')

    with instruments.SLM() as slm:
        
        print(katanalaser.idn)
        print(scanZ.idn)
        print(scanXY.idn)
        print(aotf.idn)
        # sp.Imspector() as imspector:
        # print(imspector.version())
        webcamFocusLock = instruments.CameraTIS(0, 0, 0, 0)
        webcamWidefield = instruments.CameraTIS(1, 25, 17, 725)
    
        win = control.TempestaSLMKatanaGUI(katanalaser, slm, scanZ, scanXY,
                                           webcamFocusLock, webcamWidefield,
                                           aotf)
        win.show()
        app.exec_()

def analysisApp():

    from analysis import analysis

    app = QtGui.QApplication([])

    win = analysis.AnalysisWidget()
    win.show()

    app.exec_()

