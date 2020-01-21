# -*- coding: utf-8 -*-
"""
Created on Sun Dec 28 13:25:27 2014

@author: jonatan.alvelid
"""

import importlib
from control import mockers
# import nidaqmx
# from lantz.drivers.legacy.serial import SerialDriver
# from lantz import Action, Feat


# pylint: disable=missing-docstring
# It is okay here.

class Laser():
    """An object to communicate with a laser with a Lantz driver"""
    def __new__(cls, iName, *args):
        try:
            pName, driverName = iName.rsplit('.', 1)
            package = importlib.import_module('lantz.drivers.' + pName)
            driver = getattr(package, driverName)
            laser = driver(*args)
            laser.initialize()

            return driver(*args)

        except:
            return mockers.MockLaser()


class KatanaLaser():
    def __new__(cls, *args):
        try:
            from control.katana import OneFiveLaser
            katana = OneFiveLaser(*args)
            katana.initialize()
            return katana
        except:
            print('Mock Katana loaded')
            return mockers.MockKatanaLaser()

    def __enter__(self, *args, **kwargs):
        return self.katana

    def __exit__(self, *args, **kwargs):
        self.katana.close()


class SLM():
    """This object communicates with an SLM as a second monitor,
    using a wxpython interface defined in slmpy.py.
    If no second monitor is detected, it replaces it by a Mocker
    with the same methods as the normal SLM object"""
    def __init__(self):
        super(SLM).__init__()
        try:
            from control.SLM import slmpy
            self.slm = slmpy.SLMdisplay()
        except:
            print("Mock SLM loaded")
            self.slm = mockers.MockSLM()

    def __enter__(self, *args, **kwargs):
        return self.slm

    def __exit__(self, *args, **kwargs):
        self.slm.close()


class AOTF():
    def __new__(cls, *args):
        try:
            from control.aotf import AAAOTF
            aotf = AAAOTF(*args)
            aotf.initialize()
            return aotf
        except:
            print('Mock AOTF loaded')
            return mockers.MockAAAOTF()

    def __enter__(self, *args, **kwargs):
        return self.aotf

    def __exit__(self, *args, **kwargs):
        self.aotf.close()


class LeicaStand():
    def __new__(cls, *args):
        try:
            from control.leicadmi import LeicaDMI
            leicastand = LeicaDMI(*args)
            leicastand.initialize()
            return leicastand
        except:
            print('Mock LeicaStand loaded')
            return mockers.MockLeicaDMI()

    def __enter__(self, *args, **kwargs):
        return self.leicastand

    def __exit__(self, *args, **kwargs):
        self.leicastand.close()


class ScanZ():
    def __new__(cls, *args):
        try:
            from control.zpiezo import PCZPiezo
            scan = PCZPiezo(*args)
            scan.initialize()
            return scan
        except:
            print('Mock ScanZ loaded')
            return mockers.MockPCZPiezo()

    def __enter__(self, *args, **kwargs):
        return self.scan

    def __exit__(self, *args, **kwargs):
        self.scan.close()


class XYStage():
    def __new__(cls, *args):
        try:
            from control.xystage import MHXYStage
            xyscan = MHXYStage(*args)
            xyscan.initialize()
            return xyscan
        except:
            print('Mock XYStage loaded')
            return mockers.MockMHXYStage()

    def __enter__(self, *args, **kwargs):
        return self.xyscan

    def __exit__(self, *args, **kwargs):
        self.xyscan.close()


class Webcam():
    def __new__(cls):
        webcam = mockers.MockWebcam()
        return webcam


class CameraTIS():
    def __new__(cls, *args):
        try:
            from control.cameratis import CameraTIS
            webcam = CameraTIS(*args)
            webcam.initialize()
            return webcam
        except:
            print('Mock CameraTIS loaded')
            return mockers.MockCameraTIS()

    def __enter__(self, *args, **kwargs):
        return self.webcam

    def __exit__(self, *args, **kwargs):
        self.webcam.close()
