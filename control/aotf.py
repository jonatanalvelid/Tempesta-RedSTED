# -*- coding: utf-8 -*-
"""
Created on Wed Oct 10 17:40:53 2018

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
    SEND_TERMINATION = '\r \n'

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
        """Get the product ID of the AOTF. """
        return self.query('q')

    def initialize(self):
        super().initialize()
        
        self.intensity_max = 1023  # maximum power setting for the AOTF
        
        self.query('L0' + 'I1' + 'O1')  # switch on the blanking of all the channels
        self.query('L1' + 'I1')  # switch channel 1 to internal control
        self.query('L2' + 'I1')  # switch channel 2 to internal control

    # POWER ADJUSTMENT

#    @Feat()
#    def power(self):
#        """ Get power in dBm. """
#        return float(self.query('S').split()[0])

    # Use this one, but make it better later. Measure the actual power output
    # for the different settings, fit a curve, and use the equation to
    # correlate actual output power with the setting value, and display 
    # output power.
#    @power.setter
    @Action()
    def power(self, channel, value):
        """ Power adjustment for channel X, from 0 to 1023. """
#        print('aotfpow1')
        valueaotf = round(value)  # assuming input value is [0,1023]
#        print('aotfpow2')
        if valueaotf > self.intensity_max:  # if input value higher than 1
            valueaotf = self.intensity_max
#        print('aotfpow3')
        self.query('L' + str(channel) + 'P' + str(valueaotf))
#        print('aotfpow4')

    # FREQUENCY ADJUSTMENT

    @Feat
    def frequency(self, channel):
        """ Frequnecy in MHz. """
        return float(self.query('S').split()[0])

    @frequency.setter
    def frequency(self, channel, value):
        """ Frequency adjustment for channel X, from 74 to 158 MHz. """
        self.query('L' + str(channel) + 'F' + str(value))

    # CONTROL/STATUS

    @Action()
    def channelMode(self, channel, setting):
        """ Set channel to internal (0) or external (1) operation mode. """
        self.query('L' + str(channel) + 'I' + str(setting))

    @Action()
    def driverMode(self, setting):
        """ Set global to internal (0) or external (1) operation mode. """
        self.query('I' + str(setting))

    @Action()
    def channelOn(self, channel, setting):
        """ Turn channel on (1) or off (0). """
        self.query('L' + str(channel) + 'O' + str(setting))

    def close(self):
        self.finalize()


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
    with AAAOTF('COM5') as inst:
        if args.interactive:
            from lantz.ui.qtwidgets import start_test_app
            start_test_app(inst)
        else:
            # Add your test code here
            print('Non interactive mode')
            