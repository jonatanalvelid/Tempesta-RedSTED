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
    """Driver for the PiezoConcept Z-piezo.
    """

    # flow control flags
    # RTSCTS = False
    # DSRDTR = False
    # XONXOFF = False

    ENCODING = 'ascii'

    RECV_TERMINATION = '\n'
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
        """Get information of system, such as name, number of axis,...
        maximum stroke etc. """
        return self.query('?readsn')

    def initialize(self):
        super().initialize()
        self.query('!dim 1 1')
        time.sleep(0.1)
        self.query('!resolution 6')
        time.sleep(0.1)
        self.query('!clim 65000 42500 8000')
        time.sleep(0.1)
        self.query('save')

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

    @Action(units='micrometer', limits=(100,))
    def move_absX(self, value):
        """ Absolute Z position movement, in um. """
        self.query('moa x ' + str(float(value)))

    @Action(units='micrometer', limits=(100,))
    def move_absY(self, value):
        """ Absolute Z position movement, in um. """
        self.query('moa y ' + str(float(value)))

    # CONTROL/STATUS/LIMITS

    @Feat(units='micrometer')
    def circLimit(self):
        """ Absolute Z position. """
        return self.query('?clim')

    @circLimit.setter
    def circLimit(self, xpos, ypos, radius):
        """ Absolute Z position movement, in um. """
        self.query('!clim ' + str(float(xpos)) + ' ' +
                   str(float(ypos)) + ' ' + str(float(radius)))


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
    with MHXYStage('COMXX') as inst:
        if args.interactive:
            from lantz.ui.qtwidgets import start_test_app
            start_test_app(inst)
        else:
            # Add your test code here
            print('Non interactive mode')
