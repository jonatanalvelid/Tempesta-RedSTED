# -*- coding: utf-8 -*-
"""
Created on Wed Oct 10 17:40:53 2018

@author: jonatan.alvelid
"""

# -*- coding: utf-8 -*-

"""
Created on Wed Sep  6 14:06:03 2017

@author: jonatan.alvelid

"""

from lantz import Action, Feat
from lantz.drivers.legacy.serial import SerialDriver
# from lantz.messagebased import MessageBasedDriver
# from lantz import Q_


class AAAOTF(SerialDriver):
    """Driver for the AA Optoelectronics AOTF.
    """

    ENCODING = 'ascii'

    RECV_TERMINATION = '\n'
    SEND_TERMINATION = '\n'

    BAUDRATE = 57600
    BYTESIZE = 8
    PARITY = 'none'
    STOPBITS = 1

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
        return self.query('q')

    def initialize(self):
        super().initialize()

    # POWER ADJUSTMENT

    @Feat(units='micrometer')
    def power(self, channel):
        """ Power in dBm. """
        return float(self.query('S').split()[0])

    @power.setter
    def power(self, channel, value):
        """ Power adjustment for channel X, from 0 to 1023. """
        self.query('L' + str(channel) + 'P' + str(round(value*1023)))

    # CONTROL/STATUS

    def channelMode(self, channel, setting):
        """ Set channel to internal (0) or external (1) operation mode. """
        self.query('L' + str(channel) + 'I' + str(setting))

    def driverMode(self, setting):
        """ Set global to internal (0) or external (1) operation mode. """
        self.query('I' + str(setting))

    def channelOn(self, channel, setting):
        """ Turn channel on (1) or off (0). """
        self.query('L' + str(channel) + 'O' + str(setting))

if __name__ == '__main__':
    import argparse
#    import lantz.log

    parser = argparse.ArgumentParser(description='Test Kentech HRI')
    parser.add_argument('-i', '--interactive', action='store_true',
                        default=False, help='Show interactive GUI')
    parser.add_argument('-p', '--port', type=str, default='COMXX',
                        help='Serial port to connect to')

    args = parser.parse_args()
#    lantz.log.log_to_screen(lantz.log.DEBUG)
    with AAAOTF('COMXX') as inst:
        if args.interactive:
            from lantz.ui.qtwidgets import start_test_app
            start_test_app(inst)
        else:
            # Add your test code here
            print('Non interactive mode')
            