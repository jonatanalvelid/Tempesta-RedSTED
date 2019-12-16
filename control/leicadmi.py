# -*- coding: utf-8 -*-

"""
Created on Mon Dec 16 11:58:00 2019

@author: jonatan.alvelid

"""

from lantz import Action, Feat
from lantz.drivers.legacy.serial import SerialDriver


class LeicaDMI(SerialDriver):
    """Driver for Leica DMi8 stand, mainly for controlling the z-drive and
    motorized correction collar.
    """

    ENCODING = 'ascii'

    RECV_TERMINATION = '\r'
    SEND_TERMINATION = '\r'

    BAUDRATE = 19200
    BYTESIZE = 8
    PARITY = 'none'
    STOPBITS = 1

    #: flow control flags
    RTSCTS = False
    DSRDTR = False
    XONXOFF = False

    def query(self, arg):
        return super().query(arg)[6:]

    @Feat(read_once=True)
    def idn(self):
        """Get serial number
        """
        ans = self.query('71002')
        return ans

    def initialize(self):
        super().initialize()


    # Z-MOVEMENT

    @Feat()
    def absZ(self):
        """ Absolute Z position. """
        return int(self.query('71023'))

    @absZ.setter
    def absZ(self, value):
        """ Absolute Z position movement. """
        self.query('71022 ' + str(int(value)))

    def relZ(self, value):
        """ Relative Z position movement. """
        if not int(value) == 0:
            self.query('71024 ' + str(int(value)))
            if int(value) > 132:
                print('Warning: Step bigger than 500nm.')

    @Action()
    def toFocus(self):
        """ Move Z-drive to the saved focus position. """
        self.query('71034')



    # MOT_CORR-MOVEMENT
    
    @Action()
    def motCorrPos(self, value):
        """ Absolute mot_corr position movement. """
        movetopos = int(round(value*93.83))
        self.query('47022 -1 ' + str(movetopos))



    # CONTROL

    @Feat()
    def manualCtl(self):
        """ Get manual Z-control on/off. 0 = manual off, 1 = manual on (def),
        2 = manual and PC off. """
        self.query('71006')

    @manualCtl.setter
    def manualCtl(self, value):
        """ Set manual Z-control on/off. 0 = manual off, 1 = manual on (def),
        2 = manual and PC off. """
        self.query('71005 ' + str(value))

    @Action()
    def resetUnit(self):
        """ Resets acc. param., speed param., software limits
        and focus position to default values. """
        self.query('71007')

    @Action()
    def setFocus(self, value):
        """ Sets saved focus position to a specific value. """
        self.query('71027 ' + str(value))

    @Action()
    def setFocusCurr(self):
        """ Sets current position as the saved focus position. """
        self.query('71038')

    @Action()
    def setConvFactor(self, value):
        """ Sets the conversion factor to a desired value,
        written as µm/count. """
        self.query('71043 ' + str(value))



    # STATUS

    def getStatus(self):
        """ Returns status of Z-drive as a binary code.
        "a b c d e" = "Z-drive in motion, lower hardware end switch reached,
        upper hardware end switch reached, lower threshold reached,
        focus position reached."""
        return self.query('71004')

    def getFocusPos(self):
        """ Returns the saved focus position. """
        return self.query('71029')

    def convFactor(self):
        """ Returns the conversion factor of 1 count in µm. """
        return self.query('71042')



if __name__ == '__main__':
    import argparse
#    import lantz.log

    parser = argparse.ArgumentParser(description='Test Kentech HRI')
    parser.add_argument('-i', '--interactive', action='store_true',
                        default=False, help='Show interactive GUI')
    parser.add_argument('-p', '--port', type=str, default='COM9',
                        help='Serial port to connect to')

    args = parser.parse_args()
#    lantz.log.log_to_screen(lantz.log.DEBUG)
    with LeicaDMI('COM9') as inst:
        if args.interactive:
            from lantz.ui.qtwidgets import start_test_app
            start_test_app(inst)
        else:
            # Add your test code here
            print('Non interactive mode')