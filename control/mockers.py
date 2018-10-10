# -*- coding: utf-8 -*-
"""
Created on Tue Aug 12 20:02:08 2014

@author: Federico Barabas
"""

# -*- coding: utf-8 -*-
"""
    lantz.simulators.fungen
    ~~~~~~~~~~~~~~~~~~~~~~~

    A simulated function generator.
    See specification in the Lantz documentation.

    :copyright: 2012 by The Lantz Authors
    :license: BSD, see LICENSE for more details.
"""

import logging
import numpy as np
import pygame

from lantz import Driver
from lantz import Action, Feat
from lantz import Q_

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s',
                    datefmt='%Y-%d-%m %H:%M:%S')


class constants:

    def __init__(self):
        self.GND = 0

class MockLaser(Driver):

    def __init__(self):
        super(MockLaser).__init__()

        self.mW = Q_(1, 'mW')

        self.enabled = False
        self.power_sp = 0 * self.mW

    @property
    def idn(self):
        return 'Simulated laser'

    @property
    def status(self):
        """Current device status
        """
        return 'Simulated laser status'

    # ENABLE LASER
    @property
    def enabled(self):
        """Method for turning on the laser
        """
        return self.enabled_state

    @enabled.setter
    def enabled(self, value):
        self.enabled_state = value

    # LASER'S CONTROL MODE AND SET POINT

    @property
    def power_sp(self):
        """To handle output power set point (mW) in APC Mode
        """
        return self.power_setpoint

    @power_sp.setter
    def power_sp(self, value):
        self.power_setpoint = value

    # LASER'S CURRENT STATUS

    @property
    def power(self):
        """To get the laser emission power (mW)
        """
        return 55555 * self.mW


class MockSLM(object):

    def __init__(self,monitor = 1, isImageLock = False):
        super(MockSLM).__init__()
        print('Simulated SLM')

        def getSize():
            return((792,600))

        def updateArray(mask):
            pass

        def close(self):
            pass

    def start(self):
        pass

    def get_image(self):
        arr = (100 * np.random.rand(480, 640)).astype(np.float)
        return pygame.surfarray.make_surface(arr)

    def read(self):
        return self.get_image()

    def stop(self):
        pass


class MockLeicaZDrive(object):

    def __init__(self, SerialDriver=0):
        super().__init__()
        print('Simulated Leica Z-drive')

    @Feat()
    def absZ(self):
        """ Absolute Z position. """
        pass

    @absZ.setter
    def absZ(self, value):
        """ Absolute Z position movement. """
        pass

    @Feat()
    def relZ(self):
        """ Absolute Z position. """
        pass

    @relZ.setter
    def relZ(self, value):
        """ Relative Z position movement. """
        pass


class MockPCZPiezo(object):

    def __init__(self, SerialDriver=0):
        super().__init__()
        print('Simulated PiezoConcept Z-piezo')

    @Feat()
    def absZ(self):
        """ Absolute Z position. """
        pass

    @absZ.setter
    def absZ(self, value):
        """ Absolute Z position movement. """
        pass

    @Feat()
    def relZ(self):
        """ Absolute Z position. """
        pass

    @relZ.setter
    def relZ(self, value):
        """ Relative Z position movement. """
        pass


class MockAAAOTF(object):

    def __init__(self, SerialDriver=0):
        super().__init__()
        print('Simulated AA AOTF')

    # POWER ADJUSTMENT

    @Feat()
    def power(self, channel):
        """ Power in dBm. """
        pass

    @power.setter
    def power(self, channel, value):
        """ Power adjustment for channel X, from 0 to 1023. """
        pass

    # FREQUENCY ADJUSTMENT

    @Feat
    def frequency(self, channel):
        """ Frequnecy in MHz. """
        pass

    @frequency.setter
    def frequency(self, channel, value):
        """ Frequency adjustment for channel X, from 0 to 1023. """
        pass

    # CONTROL/STATUS

    @Action()
    def channelMode(self, channel, setting):
        """ Set channel to internal (0) or external (1) operation mode. """
        pass

    @Action()
    def driverMode(self, setting):
        """ Set global to internal (0) or external (1) operation mode. """
        pass

    @Action()
    def channelOn(self, channel, setting):
        """ Turn channel on (1) or off (0). """
        pass


class MockWebcam(object):

    def __init__(self):
        super().__init__()
        print('Simulated Webcam')

    def start(self):
        pass

    def get_image(self):
        arr = (100 * np.random.rand(480, 640)).astype(np.float)
        return arr
#        return pygame.surfarray.make_surface(arr)

    def stop(self):
        pass


class MockHamamatsu(Driver):

    def __init__(self):

        self.buffer_index = 0
        self.camera_id = 9999
        self.camera_model = 'Mock Hamamatsu camera'
        self.debug = False
        self.frame_x = 500
        self.frame_y = 500
        self.frame_bytes = self.frame_x * self.frame_y * 2
        self.last_frame_number = 0
        self.properties = {}
        self.max_backlog = 0
        self.number_image_buffers = 0

        self.s = Q_(1, 's')

        # Open the camera.
#        self.camera_handle = ctypes.c_void_p(0)
#        self.checkStatus(dcam.dcam_open(ctypes.byref(self.camera_handle),
#                                        ctypes.c_int32(self.camera_id),
#                                        None),
#                         "dcam_open")
        # Get camera properties.
        self.properties = {'Name': 'MOCK Hamamatsu',
                           'exposure_time': 9999,  # * self.s,
                           'accumulation_time': 99999,  # * self.s,
                           'image_width': 2048,
                           'image_height': 2048,
                           'image_framebytes': 8,
                           'subarray_hsize': 2048,
                           'subarray_vsize': 2048,
                           'subarray_mode': 'OFF',
                           'timing_readout_time': 9999,
                           'internal_frame_rate': 9999,
                           'internal_frame_interval': 9999}

        # Get camera max width, height.
        self.max_width = self.getPropertyValue("image_width")[0]
        self.max_height = self.getPropertyValue("image_height")[0]

    def captureSetup(self):
        ''' (internal use only). This is called at the start of new acquisition
        sequence to determine the current ROI and get the camera configured
        properly.'''
        self.buffer_index = -1
        self.last_frame_number = 0

        # Set sub array mode.
        self.setSubArrayMode()

        # Get frame properties.
        self.frame_x = int(self.getPropertyValue("image_width")[0])
        self.frame_y = int(self.getPropertyValue("image_height")[0])
        self.frame_bytes = self.getPropertyValue("image_framebytes")[0]

    def checkStatus(self, fn_return, fn_name="unknown"):
        ''' Check return value of the dcam function call. Throw an error if
        not as expected?
        @return The return value of the function.'''
        pass

    def getFrames(self):
        ''' Gets all of the available frames.

        This will block waiting for new frames even if there new frames
        available when it is called.

        @return [frames, [frame x size, frame y size]]'''
        frames = []

        for i in range(2):
            # Create storage
            hc_data = HMockCamData(self.frame_x * self.frame_y)
            frames.append(hc_data)

        return [frames, [self.frame_x, self.frame_y]]

    def getModelInfo(self):
        ''' Returns the model of the camera

        @param camera_id The (integer) camera id number.

        @return A string containing the camera name.'''
        return ('WARNING!: This is a Mock Version of the Hamamatsu Orca flash '
                'camera')

    def getProperties(self):
        ''' Return the list of camera properties. This is the one to call if you
        want to know the camera properties.

        @return A dictionary of camera properties.'''
        return self.properties

    def getPropertyAttribute(self, property_name):
        ''' Return the attribute structure of a particular property.

        FIXME (OPTIMIZATION): Keep track of known attributes?

        @param property_name The name of the property to get the attributes of.

        @return A DCAM_PARAM_PROPERTYATTR object.'''
        pass

    # getPropertyText
    #
    # Return the text options of a property (if any).
    #
    # @param property_name The name of the property to get the text values of.
    #
    # @return A dictionary of text properties (which may be empty).
    #
    def getPropertyText(self, property_name):
        pass

    # getPropertyRange
    #
    # Return the range for an attribute.
    #
    # @param property_name The name of the property (as a string).
    #
    # @return [minimum value, maximum value]
    #
    def getPropertyRange(self, property_name):
        pass

    # getPropertyRW
    #
    # Return if a property is readable / writeable.
    #
    # @return [True/False (readable), True/False (writeable)]
    #
    def getPropertyRW(self, property_name):
        pass

    # getPropertyVale
    #
    # Return the current setting of a particular property.
    #
    # @param property_name The name of the property.
    #
    # @return [the property value, the property type]
    #
    def getPropertyValue(self, property_name):

        prop_value = self.properties[property_name]
        prop_type = property_name

        return [prop_value, prop_type]

    # isCameraProperty
    #
    # Check if a property name is supported by the camera.
    #
    # @param property_name The name of the property.
    #
    # @return True/False if property_name is a supported camera property.
    #
    def isCameraProperty(self, property_name):
        if (property_name in self.properties):
            return True
        else:
            return False

    # newFrames
    #
    # Return a list of the ids of all the new frames since the last check.
    #
    # This will block waiting for at least one new frame.
    #
    # @return [id of the first frame, .. , id of the last frame]
    #
    def newFrames(self):

        # Create a list of the new frames.
        new_frames = [0]

        return new_frames

    # setPropertyValue
    #
    # Set the value of a property.
    #
    # @param property_name The name of the property.
    # @param property_value The value to set the property to.
    #
    def setPropertyValue(self, property_name, property_value):

        # Check if the property exists.
        if not (property_name in self.properties):
            return False

        # If the value is text, figure out what the
        # corresponding numerical property value is.

        self.properties[property_name] = property_value
#        print(property_name, 'set to:', self.properties[property_name])
#            if (property_value in text_values):
#                property_value = float(text_values[property_value])
#            else:
#                print(" unknown property text value:", property_value, "for",
#                      property_name)
#                return False
        return property_value

    # setSubArrayMode
    #
    # This sets the sub-array mode as appropriate based on the current ROI.
    #
    def setSubArrayMode(self):

        # Check ROI properties.
        roi_w = self.getPropertyValue("subarray_hsize")[0]
        roi_h = self.getPropertyValue("subarray_vsize")[0]
        self.properties['image_height'] = roi_h
        self.properties['image_width'] = roi_w

        # If the ROI is smaller than the entire frame turn on subarray mode
        if ((roi_w == self.max_width) and (roi_h == self.max_height)):
            self.setPropertyValue("subarray_mode", "OFF")
        else:
            self.setPropertyValue("subarray_mode", "ON")

    # startAcquisition
    #
    # Start data acquisition.
    #
    def startAcquisition(self):
        self.captureSetup()
        n_buffers = int((2.0 * 1024 * 1024 * 1024) / self.frame_bytes)
        self.number_image_buffers = n_buffers

        self.hcam_data = []
        for i in range(1, 2):
            hc_data = HMockCamData(self.frame_x * self.frame_y)
            self.hcam_data.append(hc_data)

        print('size of hcam_data = ', np.size(self.hcam_data))

    # stopAcquisition
    #
    # Stop data acquisition.
    #
    def stopAcquisition(self):
        pass

    # shutdown
    #
    # Close down the connection to the camera.
    #
    def shutdown(self):
        pass