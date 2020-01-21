# -*- coding: utf-8 -*-
"""
Created on Mon Jan 23 15:20:04 2017

@author: STEDred, jonatanalvelid
"""

from pyqtgraph.Qt import QtGui
from control import control, instruments

def main():
    """Main function. Instantiate main hardware components, and send these to the main GUI.
    """
    app = QtGui.QApplication([])

    leica_stand = instruments.LeicaStand('COM9')
    katana_laser = instruments.KatanaLaser('COM8')
    scan_z = instruments.ScanZ('COM5')
    scan_xy = instruments.XYStage('COM6')
    aotf = instruments.AOTF('COM4')

    with instruments.SLM() as slm:
        
        print(katana_laser.idn)
        print(scan_z.idn)
        print(scan_xy.idn)
        print(aotf.idn)
        webcam_focus_lock = instruments.CameraTIS(0, 0, 0, 0)
        webcam_widefield = instruments.CameraTIS(1, 25, 17, 725)
    
        win = control.TempestaSLMKatanaGUI(katana_laser, slm, scan_z, scan_xy,
                                           webcam_focus_lock, webcam_widefield,
                                           aotf, leica_stand)
        win.show()
        app.exec_()
