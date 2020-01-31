# -*- coding: utf-8 -*-
"""
Created on Wed Oct 24 13:47:16 2018

@author: jonatan.alvelid
"""


# import math
import time
# from pyvisa import constants

from lantz import Action, Feat
# from lantz.messagebased import MessageBasedDriver
from lantz.drivers.legacy.serial import SerialDriver
# from lantz import Q_


class MHXYStage(SerialDriver):
    """Driver for the Marzhauser XY-stage.
    """

    # flow control flags
    # RTSCTS = False
    # DSRDTR = False
    # XONXOFF = False

    ENCODING = 'ascii'

    RECV_TERMINATION = ''
    SEND_TERMINATION = '\n'

    BAUDRATE = 57600
    BYTESIZE = 8
    PARITY = 'none'
    STOPBITS = 2

    #: flow control flags
    RTSCTS = False
    DSRDTR = False
    XONXOFF = False

    def query(self, arg):
        return super().query(arg)

    @Feat(read_once=True)
    def idn(self):
        """Read serial number of stage. """
        print(str(self.query('?readsn')))
        return str(self.query('?readsn'))

    def initialize(self):
        super().initialize()
        self.query('!dim 1 1')  # Set the dimensions of all commands to um
        time.sleep(0.1)
        self.query('!resolution 6')  # Set the read position resolution to nm
        time.sleep(0.1)
        self.query('!clim 0 0 25000')  # Set circular limits to the movement
        # range, centered at 0,0 with a radius of 10000 µm (10 mm).
        time.sleep(0.1)
        print(self.query('save'))  # Save settings to the controller
        time.sleep(0.1)
        #print(self.query('moc'))  # Move the stage to the center position, in case it
        # has moved from there after being switched off. Eventually change this
        # to the actual center of most cover slips! 
        #time.sleep(0.1)

    # XY-POSITION READING AND MOVEMENT

    @Feat(units='micrometer')
    def absX(self):
        """ Read absolute X position, in um. """
        return float(self.query('?pos x'))

    @Feat(units='micrometer')
    def absY(self):
        """ Read absolute Y position, in um. """
        return float(self.query('?pos y'))

    @Action(units='micrometer')
    def move_relX(self, value):
        """ Relative X position movement, in um. """
        self.query('mor x ' + str(float(value)))

    @Action(units='micrometer')
    def move_relY(self, value):
        """ Relative Y position movement, in um. """
        self.query('mor y ' + str(float(value)))

#    @Action(units='micrometer')
#    def move_rel(self, valuex, valuey):
#        """ Relative position movement, in um. """
#        self.query('mor ' + str(float(valuex)) + ' ' + str(float(valuey)))

    @Action(units='micrometer', limits=(100,))
    def move_absX(self, value):
        """ Absolute X position movement, in um. """
        self.query('moa x ' + str(float(value)))

    @Action(units='micrometer', limits=(100,))
    def move_absY(self, value):
        """ Absolute Y position movement, in um. """
        self.query('moa y ' + str(float(value)))

    # CONTROL/STATUS/LIMITS

    @Feat(units='micrometer')
    def circLimit(self):
        """ Circular limits, in terms of X,Y center and radius. """
        return self.query('?clim')

    @circLimit.setter
    def circLimit(self, xpos, ypos, radius):
        """ Set circular limits, in terms of X,Y center and radius. """
        self.query('!clim ' + str(float(xpos)) + ' ' +
                   str(float(ypos)) + ' ' + str(float(radius)))
     
    @Action()
    def function_press(self):
        """ Absolute X position movement, in um. """
        button_status = self.query('?keyl').split()
        button_status = list(map(int, button_status))
        return button_status

    def close(self):
        self.finalize()


if __name__ == '__main__':
    import argparse
#    import lantz.log

    parser = argparse.ArgumentParser(description='Test Märzhäuser XY-stage')
    parser.add_argument('-i', '--interactive', action='store_true',
                        default=False, help='Show interactive GUI')
    parser.add_argument('-p', '--port', type=str, default='COMXX',
                        help='Serial port to connect to')

    args = parser.parse_args()
#    lantz.log.log_to_screen(lantz.log.DEBUG)
    with MHXYStage('COM6') as inst:
        if args.interactive:
            from lantz.ui.qtwidgets import start_test_app
            start_test_app(inst)
        else:
            # Add your test code here
            print('Non interactive mode')
