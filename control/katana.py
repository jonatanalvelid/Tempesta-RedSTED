# -*- coding: utf-8 -*-
"""
Created on Tue Nov 5 09:28:55 2019

Katana Serial Driver

@author: STEDred
"""
#TODO: Fix this driver.
class OneFiveLaser(object):
    """class used to control the 775 nm laser via a RS 232 interface. The commands are defined
    in the laser manual, must be binary and end with an LF statement

    :param string port: specifies the name of the port to which the laser is connected (usually COM10).
    :param float intensity_max: specifies the maximum intensity (in our case in W) the user can ask the laser to emit. It is used to protect sensitive hardware from high intensities
    """

    def __init__(self, port="COM10", intensity_max=0.8):
        self.serial_port = None
        self.info = None      # Contains informations about the different methods of the laser. Can be used that the communication works
        self.power_setting = 0    # To change the power with python
        self.intensity_max = intensity_max
        self.mode = 0     # Constant current or Power
        self.triggerMode = 0        # Trigger=TTL input
        self.enabled_state = False    # Laser initially off
        self.mW = Q_(1, 'mW')
        self.power_setpoint = 0
        self.power_sp = 0*self.mW

        try:
            import serial
            print('OneFiveLaser 1')
            self.serial_port = serial.Serial(
                 port=port,
                 baudrate=38400,
                 stopbits=serial.STOPBITS_ONE,
                 bytesize=serial.EIGHTBITS
                 )
#            self.getInfo()
            print('OneFiveLaser 2')
            self.setPowerSetting()
#            self.mode=self.getMode()
            self.setPowerSetting(self.power_setting)
            self.setTriggerSource(self.triggerMode)
            print('OneFiveLaser 3')
#        except serial.SerialException or serial.SerialTimeoutException:
        except:
            print('Mock OneFiveLaser loaded')
            self = mockers.MockKatanaLaser()

    @property
    def idn(self):
        return 'OneFive 775nm'

    @property
    def status(self):
        """Current device status
        """
        return 'OneFive laser status'

    @property
    def enabled(self):
        """Method for turning on the laser
        """
        return self.enabled_state

    @enabled.setter
    def enabled(self, value):
        cmd = "le=" + str(int(value)) + "\n"
        self.serial_port.write(cmd.encode())
        self.enabled_state = value

    # LASER'S CONTROL MODE AND SET POINT

    @property
    def power_sp(self):
        """To handle output power set point (mW)
        """
        return self.power_setpoint * 100 * self.mW

    @power_sp.setter
    def power_sp(self, value):
        """Handles output power. Sends a RS232 command to the laser specifying the new intensity."""
        value = value.magnitude/1000  # Conversion from mW to W
        if(self.power_setting != 1):
            print("Wrong mode: impossible to change power value. Please change the power settings")
            return
        if(value < 0):
            value = 0
        if(value > self.intensity_max):
            value = self.intensity_max  # A too high intensity value can damage the SLM
        value = round(value, 3)
        cmd = "lp=" + str(value) + "\n"
        self.serial_port.write(cmd.encode())
        self.power_setpoint = value

    # LASER'S CURRENT STATUS

    @property
    def power(self):
        """To get the laser emission power (mW)
        """
        return self.intensity_max * 100 * self.mW

    def getInfo(self):
        """Returns available commands"""
        if self.info is None:
            self.serial_port.write(b"h\n")
            time.sleep(0.5)
            self.info = self.serial_port.read_all().decode()
        else:
            print(self.info)

    def setPowerSetting(self, manual=1):
        """if manual=0, the power can be changed via this interface
        if manual=1, it has to be changed by turning the button (manually)"""
        if(manual != 1 and manual != 0):
            print("setPowerSetting: invalid argument")
            self.power_setting = 0
        self.power_setting = manual
        value = "lps" + str(manual) + "\n"
        self.serial_port.write(value.encode())


    def setMode(self, value) :
        """value=1: constant current mode
        value=0 : constant power mode"""
        if(value != 1 and value != 0):
            print("wrong value")
            return
        self.mode = value
        cmd = "lip=" + str(value) + "\n"
        self.serial_port.write(cmd.encode())

    def setCurrent(self,value):
        """sets current in constant current mode."""
        if (self.mode!=1):
            print("You can't set the current in constant power mode")
            return
        if(value<0):
            value=0
        if(value>6):
            value=6 #Arbitrary limit to not burn the components
        value=round(value,2)
        cmd="li="+str(value)+"\n"
        self.serial_port.write(cmd.encode())

    def setFrequency(self,value):
        """sets the pulse frequency in MHz"""
        if(value<18 or value>80):
            print("invalid frequency values")
            return
        value*=10**6
        cmd="lx_freq="+str(value)+"\n"
        self.serial_port.write(cmd.encode())

    def setTriggerSource(self,source):
        """source=0: internal frequency generator
        source=1: external trigger source for adjustable trigger level, Tr-1 In
        source=2: external trigger source for TTL trigger, Tr-2 In
        """
        if(source!=0 and source!=1 and source!=2):
            print("invalid source for trigger")
            return
        cmd="lts="+str(source)+"\n"
        self.triggerMode=source
        self.serial_port.write(cmd.encode())

    def setTriggerLevel(self,value):
        """defines the trigger level in Volts, between -5 and 5V"""
        if(np.absolute(value)>5):
            print("incorrect value")
            return
        if(self.triggerMode!=1):
            print("impossible to change the \
            trigger level with this trigger. Please change the trigger source first")
            return
        value=round(value,2)
        cmd="ltll="+str(value)+"\n"
        self.serial_port.write(cmd.encode())

        #The get... methods return a string giving information about the laser
    def getPower(self):
        """Returns internal measured Laser power"""
        self.serial_port.flushInput()
        self.serial_port.write(b"lpa?\n")
        value=self.serial_port.readline().decode()
        return value

    def getMode(self):
        """Returns mode of operation: constant current or current power"""
        self.serial_port.flushInput()
        self.serial_port.write(b"lip?\n")
        value=self.serial_port.readline().decode()
        if(value=="lip=0\n"):
            value="Constant power mode"
        else:
            value="Constant current mode"
        return value

    def getPowerCommand(self):
        """gets the nominal power command in W"""
        self.serial_port.flushInput()
        self.serial_port.write(b"lp?\n")
        value=self.serial_port.readline().decode()
        return "power command: "+value+"W"

    def getTemperature(self):
        """Gets Temperature of SHG cristal"""
        self.serial_port.flushInput()
        self.serial_port.write(b"lx_temp_shg?\n")
        value=self.serial_port.readline().decode()
        return value

    def getCurrent(self):
        """Returns actual current"""
        self.serial_port.flushInput()
        self.serial_port.write(b"li?\n")
        value=self.serial_port.readline().decode()
        return value

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.close()

    def close(self):
        pass
#        self.enabled = False
#        self.serial_port.close()
     