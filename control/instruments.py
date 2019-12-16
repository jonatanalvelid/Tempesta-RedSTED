# -*- coding: utf-8 -*-
"""
Created on Sun Dec 28 13:25:27 2014

@author: jonatan.alvelid
"""

import numpy as np
import importlib
import control.mockers as mockers
# import nidaqmx
# from lantz.drivers.legacy.serial import SerialDriver
# from lantz import Action, Feat


class Laser(object):
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


class KatanaLaser(object):
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


class SLM(object):
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


class AOTF(object):
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


class LeicaStand(object):
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


class ScanZ(object):
    def __new__(cls, *args):
        try:
            from control.zpiezo import PCZPiezo
            scan = PCZPiezo(*args)
            scan.initialize()
            return scan
        except:
            print('Mock ScanZ loaded')
            return mockers.MockPCZPiezo()

#    def __init__(self, *args):
#        try:
#            from control.zpiezo import PCZPiezo
#            self.scan = PCZPiezo(*args)
#            self.scan.initialize()
#            return self.scan
#        except:
#            print('Mock ScanZ loaded')
#            return mockers.MockPCZPiezo()

    def __enter__(self, *args, **kwargs):
        return self.scan

    def __exit__(self, *args, **kwargs):
        self.scan.close()


class XYStage(object):
    # new instead of init, we want an instsance of the class to be returned
    def __new__(cls, *args):
        try:
            from control.xystage import MHXYStage
            xyscan = MHXYStage(*args)
            xyscan.initialize()
            return xyscan
        except:
            print('Mock XYStage loaded')
            return mockers.MockMHXYStage()

#    def __init__(self, *args):
#        try:
#            from control.xystage import MHXYStage
#            self.xyscan = MHXYStage(*args)
#            self.xyscan.initialize()
#            return self.xyscan
#        except:
#            print('Mock XYStage loaded')
#            return mockers.MockMHXYStage()


    def __enter__(self, *args, **kwargs):
        return self.xyscan

    def __exit__(self, *args, **kwargs):
        self.xyscan.close()


class Webcam(object):
    def __new__(cls):
        webcam = mockers.MockWebcam()
        return webcam


class CameraTIS(mockers.MockHamamatsu):
    def __init__(self, cameraNo, exposure, gain, brightness):
        super().__init__()

        self.properties['subarray_vpos'] = 0
        self.properties['subarray_hpos'] = 0
        self.properties['exposure_time'] = 0.03
        self.properties['subarray_vsize'] = 1024
        self.properties['subarray_hsize'] = 1280

        from pyicic import IC_ImagingControl
        ic_ic = IC_ImagingControl.IC_ImagingControl()
        ic_ic.init_library()
        cam_names = ic_ic.get_unique_device_names()
        print(cam_names)
        self.cam = ic_ic.get_device(cam_names[cameraNo])
        # print(self.cam.list_property_names())

        self.cam.open()

        self.cam.colorenable = 0
        self.cam.gain.auto = False
        self.cam.exposure.auto = False
        if cameraNo == 1:
            self.cam.exposure = exposure  # exposure in ms
            self.cam.gain = gain  # gain in dB
            self.cam.brightness = brightness  # brightness in arbitrary units
            self.properties['subarray_vsize'] = 2048
            self.properties['subarray_hsize'] = 2448
        self.cam.enable_continuous_mode(True)  # image in continuous mode
        self.cam.start_live(show_display=False)  # start imaging
        # self.cam.enable_trigger(True)  # camera will wait for trigger
        # self.cam.send_trigger()
        if not self.cam.callback_registered:
            self.cam.register_frame_ready_callback()  # needed to wait for frame ready callback

    def grab_image(self):
        self.cam.reset_frame_ready()  # reset frame ready flag
        self.cam.send_trigger()
        # self.cam.wait_til_frame_ready(0)  # wait for frame ready due to trigger
        frame = self.cam.get_image_data()
        # y0 = self.properties['subarray_vpos']
        # x0 = self.properties['subarray_hpos']
        # y_size = self.properties['subarray_vsize']
        # x_size = self.properties['subarray_hsize']
        # now = time.time()
        # Old way, averaging the RGB image to a grayscale. Very slow for the big camera (2480x2048).
        #frame = np.average(frame, 2)
#        print(type(frame))
#        print(frame)
        # New way, just take the R-component, this should anyway contain most information in both cameras. Change this if we want to look at another color, like GFP!
        frame = np.array(frame[0], dtype='float64')
        # Check if below is giving the right dimensions out
        frame = np.reshape(frame,(self.properties['subarray_vsize'],self.properties['subarray_hsize'],3))[:,:,0]
        # print(frame)
        # now = time.time()
        # print("Avg RGB took: ", now-then, " seconds")
        # return frame_cropped
        # print(x_size)
        # print(y_size)
        # frame_cropped = np.average(frame[0:0+x_size, 0:0+y_size], 2)
        # return frame_cropped
        return frame

    def setPropertyValue(self, property_name, property_value):
        # Check if the property exists.
        if not (property_name in self.properties):
            print('Property', property_name, 'does not exist')
            return False

        # if property_name == 'exposure_time':

        # If the value is text, figure out what the
        # corresponding numerical property value is.

        self.properties[property_name] = property_value
        return property_value

    def show_dialog(self):
        self.cam.show_property_dialog()
