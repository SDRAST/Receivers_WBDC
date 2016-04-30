"""
Module WBDC.WBDC2 provides class WBDC2

Overview
========

For a description of the generic Wide Band Down Converter see/do
MonitorControl.Receivers.WBDC.__doc__.split('\n')

WBDC2 has two signal input pairs, each accepting two orthogonal linear
polarizations. There are two down-converter chains, each handling two
polarizations each, for a total of four complex signals.

Monitor and control is done with LabJacks. For a detailed description of
the LabJack see/do
MonitorControl.Electronics.Interfaces.LabJack.__doc__.split('\n')

The LabJack with local ID 1 controls and reads switches and reads analog
data (currents, voltages, temperatures) on the motherboard. Details are
described in
/home/kuiper/DSN/technical/Band K/Kband-downconv/Smith-Weinreb/\
WBDC2/DigitalBoard/ControlLogic.ods

LabJacks 2 and 3 control attenuators using TickDACs to provide analog control
voltages.

Motherboard Control
===================

Motherboard signals are monitored and controlled with digital latches (logical
devices which preserve a specified logic state). The latches are connected to
serial-in/parallel-out registers.  These registers are addressed using the EIO
out bits of LabJack 1.  The data are then clocked into the register using
the SDI and SCK signals.  The details are described in the module 'latchgroup'.

WBDC2 has two digital modules (DM 1 and DM 2).  For each DM, four latch groups
are designated by their circuit name (LG 1 through LG 4). The docstring for
module 'latchgroup' describes the latch group addressing scheme.  Bit 2 selects
a latch for reading if set, or writing if not set.  (In other words, the read
address is the write address + 4.)

Digital Module 1
----------------

Feed Crossover Switch
~~~~~~~~~~~~~~~~~~~~~

The feed crossover switches are controlled with DM 1 LG 1 using bits L1A0 and
L1A1 (A0, A1 at latchgroup address 8)::
  0 for through
  1 for crossed
The commanded state can be read at the same bits (A0, A1 at LG address 12).
However, the actual state of the cross-over switches are read at L4A0 and
L4A1 (LG address 15).

Polarization Hybrids
~~~~~~~~~~~~~~~~~~~~

The receiver chain 1 polarization hybrids are controlled by L2A0-L2A4.
The receiver chain 2 polarization hybrids are controlled by L3A0-L4A4.
Logic level 0 is for bypassing the hybrids, that is, linear polarization.
Logic level 1 is for converting linear to circular, that is, X and Y
polarization to L and R (though the sign of that needs to be verified).::
  Band  Control Bits
   18    L2A4 L3A0
   20    L2A3 L3A1
   22    L2A2 L3A2
   24    L2A1 L3A3
   26    L2A0 L3A4

Digital Module 2
----------------

Latch Groups 1,2,3,4 (Address 160,161,162,163)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Receiver chain 1 IQ hybrids are controlled by high address latch groups 1 and 2
Receiver chain 2 IQ hybrids are controlled by high address latch groups 3 and 4
The two switches use opposite logic
Logic level 1,0 is for IQ; logic level 0,1 is for LU::
          Pol 1        Pol 2
  Band  Rec1  Rec2   Rec1  Rec2
   18   L2A4  L2A3   L3A0  L3A1
   20   L2A2  L2A1   L3A2  L3A3
   22   L1A5  L1A4   L3A4  L3A5
   24   L1A3  L1A2   L4A1  L4A2
   26   L1A1  L1A0   L4A3  L4A4


Motherboard Monitoring
======================

Digital Module 1
----------------

Seven latch groups are assigned to digital monitoring, that is, the program
reads the latch states.

Low Address Latch Groups 2 (Address 85) and 3 (Address 86)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The receiver chain 1 polarization hybrids are monitored by L2A0-L2A4.
The receiver chain 2 polarization hybrids are monitored by L3A0-L4A4.
Logic level 0 is the hybrids are bypassed; logic level 1 shows the hybrids are
converting X and Y polarization to L and R.::
  Band  Control Bits
   18    L2A4 L3A0
   20    L2A3 L3A1
   22    L2A2 L3A2
   24    L2A1 L3A3
   26    L2A0 L3A4

Low Address Latch Group 4 (Address 87)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This monitors the state of the transfer switches and the local oscillator
phase-locked loops::
  Pol   Status Bit
    X      L4A0
    Y      L4A1
  Band  Status Bit
   18      L4A2
   20      L4A3
   22      L4A4
   24      L4A5
   26      L4A6

Digital Module 2
----------------

High Address Latch Groups 1-4 (Addresses 164-168)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Receiver chain 1 IQ hybrids are monitored by high address latch groups 1 and 2
Receiver chain 2 IQ hybrids are monitores by high address latch groups 3 and 4
The two switches use opposite logic
Logic level 1,0 is for IQ; logic level 0,1 is for LU::
          Pol 1        Pol 2
  Band  Rec1  Rec2   Rec1  Rec2
   18   L2A4  L2A3   L3A0  L3A1
   20   L2A2  L2A1   L3A2  L3A3
   22   L1A5  L1A4   L3A4  L3A5
   24   L1A3  L1A2   L4A1  L4A2
   26   L1A1  L1A0   L4A3  L4A4

Latch LEDs
~~~~~~~~~~
The monitor bits should match the LEDs to the top right of the motherboard.
With the hinge of the lid at the bottom the LEDs are in LSB -> MSB order
and grouped as::
  LATCH86 LATCH87
  LATCH84 LATCH85
If the box is mounted on a wall or ceiling and the lid is hanging down,
the order is more conventional.

Analog Monitoring
-----------------

Latch 1 (Address 0)
~~~~~~~~~~~~~~~~~~~
This latch selects voltage and current monitoring points.  Voltage points are
selected using bits 0-2 and read at AIN1.  Currents are selected using bits
3-6 and read at AIN0.  The addresses can be ANDed to select any voltage point
with any current point.
Voltages::
 0 ---- 000  +6 V digital *  4.0211
 0 ---- 001  +6 V analog  *  4.0278
 0 ---- 010 +16 V DC      * 10.5446
 0 ---- 011 +12 V DC      * 10.5827
 0 ---- 100 -16 V DC      *-10.5446
The actual voltages are the data times the scale factor shown above.
Currents::
 0 0000 ---  +6 V Digital MB
 0 0001 ---  +6 V Analog MB
 0 0010 --- -16 V MB
 0 0011 --- +16 V R1 FE
 0 0100 --- +16 V R2 FE
 0 0101 --- +16 V R1 BE
 0 0110 --- +16 V R2 BE
 0 0111 --- +16 V LDROs
 0 1000 --- +16 V MB
 0 1001 ---  +6 V R1 FE
 0 1010 ---  +6 V R2 FE
 0 1011 --- -16 V R1 FE
 0 1100 --- -16 V R2 FE
 0 1101 --- -16 V R1 BE
 0 1110 --- -16 V R2 BE
The actual currents (in mA?) are (data - 0.026)*1

Latch 2 (Address 1)
~~~~~~~~~~~~~~~~~~~
This latch selects temperatures (bits 0-2) read at AIN3 and RF detector
voltages (bits 3-6) read at AIN2.

Temperatures::
 0 ---- 000 R1 RF plate
 0 ---- 001 R2 RF plate
 0 ---- 010 BE plate
The temperature in deg C is (data+0.2389275)*23.549481

Detectors::
 0 0000 --- R1 E
 0 1000 --- R2 E
 0 0100 --- R1 H
 0 1100 --- R2 H
The actual reading is (data-0.004)*2.0064

Attenuators
-----------

There are ten RF voltage-controlled attenuators (PIN diodes) for each
down-converter sub-band.  The twenty voltages are generated in LabJack
TickDACs attached to LabJacks 2 and 3.

LabJack Configuration
=====================

LabJack 1
---------
Functions::
  FIO0-FIO3 - AIN: monitor voltages, current, temperatures
  FIO4-FIO6 -      not used
  FIO7      - DO:  read digital in
  EIO0-EIO7 - DO:  select latch by address
  CIO0-CIO3 - DO:  set WBDC signals

So this is the LabJack Configuration::
              CIOBitDir     1111
              EIOBitDir 11111111
              FIOBitDir 00000000
              FIOAnalog 00001111

Latch Addresses 0 and 2
~~~~~~~~~~~~~~~~~~~~~~~
There are a number of registers used to select analog monitoring points.
bit pattern sent to latch address 0 selects a current and a voltage
to be connected to AIN0 and AIN1.  A bit pattern sent to latch address
2 selects a thermistor to be connected to AIN2.  AIN3 is not used in this
receiver.

LabJack 2 and 3 Typical Configuration
-------------------------------
An initial checkout might be::
  In [2]: from Observatory import WBDC
  In [3]: lj = connect_to_U3s()

The normal state of the U3s is something like::
          U3 local ID          1        2
          ------------- -------- --------
              CIOBitDir 00001111 00000000
               CIOState 00001111 00001111
             DAC1Enable 00000000 00000000
              EIOAnalog 00000000 00000000
               EIOState 01010111 11111111
         EnableCounter0    0.000    0.000
         EnableCounter1    0.000    0.000
                  FAIN0    0.001
                  FAIN1    1.455
                  FAIN2    0.000
                  FAIN3    0.000
              FIOAnalog 00001111 00000000
              FIOBitDir 00000000 00000000
               FIOState 11110000 11111111
  NumberOfTimersEnabled        0        0
          Temperature  295.569  295.507
     TimerCounterConfig       64       64
  TimerCounterPinOffset        4        4
"""
import logging
import u3
import re
import os.path

import Math
from .... import MCobject, MCgroup, ObservatoryError
from ..WBDC_core import LatchGroup
from Electronics.Instruments.PINatten import PINattenuator, get_splines
from Electronics.Interfaces.LabJack import connect_to_U3s, LJTickDAC

module_logger = logging.getLogger(__name__)
package_dir = "/usr/local/lib/python2.7/DSN-Sci-packages/"
module_subdir = "MonitorControl/Receivers/WBDC/WBDC2/"

class WBDC2hwif(MCobject):
  """
  Provides hardware interface to WBDC2
  """
  pol_names  = ["E",  "H" ]
  RF_names   = ["R1", "R2"]
  out_pols   = ["P1", "P2"]
  DC_names   = ["D1", "D2"]
  IF_names   = ["I1", "I2"]
  bands      = ["18", "20", "22", "24", "26"]
  LJIDs = {320053997: 1, 320052373: 2, 320059056: 3}
  mon_points = {
    1: {1: (int('0000000', 2), " +6 V digitalMB", " +6 V dig"),
        2: (int('1000001', 2), " +6 V analog MB", " +6 V ana"),
        3: (int('0001010', 2), "+16 V MB"       , "+16 V"),
        4: (int('0000011', 2), ""               , "+12 V"),
        5: (int('0100100', 2), "-16 V MB"       , "-16 V"),
        6: (int('1100010', 2), "+16 V R1 FE"    , "+16 V"),
        7: (int('0010010', 2), "+16 V R2 FE"    , "+16 V"),
        8: (int('1010010', 2), "+16 V R1 BE"    , "+16 V"),
        9: (int('0110010', 2), "+16 V R2 BE"    , "+16 V"),
       10: (int('1110010', 2), "+16 V LDROs"    , "+16 V"),
       11: (int('1001001', 2), " +6 V R1 FE"    , " +6 V ana"),
       12: (int('0101001', 2), " +6 V R2 FE"    , " +6 V ana"),
       13: (int('1101100', 2), "-16 V R1 FE"    , "-16 V"),
       14: (int('0011100', 2), "-16 V R2 FE"    , "-16 V"),
       15: (int('1011100', 2), "-16 V R1 BE"    , "-16 V"),
       16: (int('0111100', 2), "-16 V R2 BE"    , "-16 V")},
   2: { 1: (int('0000000', 2), "R1 E-plane"     , "R1 RF plate"),
        2: (int('1000001', 2), "R2 E-plane"     , "R2 RF plate"),
        3: (int('0100010', 2), "R1 H-plane"     , "BE plate"),
        4: (int('1100000', 2), "R2 H-plane"     , "") } }

  splines_lab = get_splines(package_dir+module_subdir+"splines-lab.pkl")
  splines_file = package_dir+module_subdir+"splines.pkl"
  if os.path.exists(splines_file):
    splines = get_splines(splines_file)
  else:
    splines = splines_lab

  def __init__(self, name, active=True):
    """
    Initialize a WBDC2 object.

    @param name : unique identifier
    @type  name : str

    @param active : True is the FrontEnd instance is functional
    @type  active : bool
    """
    self.name = name
    self.logger = logging.getLogger(module_logger.name+".WBDC2hwif")
    self.logger.debug("\ninitializing %s", self)

    self.LJ = connect_to_U3s(WBDC2hwif.LJIDs)
    if self.has_labjack(1):
      self.configure_MB_labjack()
    else:
      raise WBDCerror("could not configure motherboard Labjack")

    # Define the latch groups
    self.lg = {'A1':    LatchGroup(parent=self, DM=0, LG=1),
               'A2':    LatchGroup(parent=self, DM=0, LG=2)}
    self.lg['X'] =    LatchGroup(parent=self, LG=1)        # crossover (X) switch
    self.lg['R1P'] =  LatchGroup(parent=self, LG=2)        # R1 pol hybrid control
    self.lg['R2P'] =  LatchGroup(parent=self, LG=3)
    self.lg['PLL'] =  LatchGroup(parent=self, LG=4)
    self.lg['R1I1'] = LatchGroup(parent=self, DM=2, LG=1)
    self.lg['R1I2'] = LatchGroup(parent=self, DM=2, LG=2)
    self.lg['R2I1'] = LatchGroup(parent=self, DM=2, LG=3)
    self.lg['R2I2'] = LatchGroup(parent=self, DM=2, LG=4)

    # The first element in a WBDC is the two-polarization feed transfer switch
    self.crossSwitch = self.TransferSwitch(self, "WBDC transfer switch")

    self.pol_sec = {}
    for band in WBDC2hwif.bands:
      for rx in WBDC2hwif.RF_names:
        psec_inputs = {}
        psec_name = rx+'-'+band
        self.pol_sec[psec_name] = self.PolSection(self, psec_name)
        self.pol_sec[psec_name].data['band'] = band
        self.pol_sec[psec_name].data['receiver'] = rx
        self.pol_sec[psec_name].get_state()
    pol_sec_names = self.pol_sec.keys()
    pol_sec_names.sort()
    self.logger.debug(" __init__: pol sections: %s", pol_sec_names)

    self.DC = {}
    for name in pol_sec_names:
      for pol in WBDC2hwif.out_pols:
        self.logger.debug(" making DC for %s", name+pol)
        self.logger.debug(" creating inputs for %s", name+pol)
        self.DC[name+pol] = self.DownConv(self, name+pol)
        rx,band = name.split('-')
        self.DC[name+pol].data['receiver'] = rx
        self.DC[name+pol].data['band'] = band
        self.DC[name+pol].data['pol'] = pol
        self.DC[name+pol].get_state()
        self.logger.debug(" DC %s created", self.DC[name+pol])

    self.analog_monitor = self.AnalogMonitor(self, WBDC2hwif.mon_points)
    self.logger.debug(" initialized for %s", self.name)
    
  def get_Xswitch_state(self):
    """
    Returns the state of the cros-over switches
    
    Response is a dict with the state of the switch for each pol
    """
    return self.crossSwitch.get_state()
    
  def get_pol_sec_states(self):
    """
    """
    states = {}
    for key in self.pol_sec.keys():
      states[key] = self.pol_sec[key].get_state()
    return states

  def set_atten_volts(self, ID, attenID, volts):
    """
    """
    self.pol_sec[ID].atten[attenID].set_voltage()
    
  def get_DC_states(self):
    states = {}
    for key in self.DC.keys():
      states[key] = self.DC[key].get_state()
    return states
      
  class TransferSwitch(MCobject):
    """
    Beam to down-converter transfer switch

    There is one Switch object for each front-end polarization P1 and P2.


    At some point this might become a general transfer switch class
    """
    def __init__(self, parent, name):
      mylogger = logging.getLogger(parent.logger.name+".TransferSwitch")
      self.name = name
      self.parent = parent
      self.logger = mylogger
      self.logger.debug(" initializing %s", self)
      self.states = {}
      self.data = {}
      for key in [1,2]:
        self.data[key] = self.Xswitch(self, str(key))       

    def get_state(self):
      """
      Get the state of the beam cross-over switches
      """
      keys = self.data.keys()
      self.logger.debug("get_state: checking switches %s", keys)
      keys.sort()
      for ID in keys:
        self.states[ID] = self.data[ID].state
      if self.states[keys[0]] != self.states[keys[1]]:
        self.logger.error("%s sub-switch states do not match",str(self))
      self.state = self.states[keys[0]]
      self.logger.debug("get_state: %s state is %s",
                        self, self.state)
      return self.state

    def set_state(self, crossover=False):
      """
      Set the RF transfer (crossover) switch
      """
      self.state = crossover
      keys = self.data.keys()
      keys.sort()
      for ID in keys:
        self.states[ID] = self.data[ID].set_state(crossover)
      self.get_state()
      self.logger.debug("set_state: %s state is %s", self, self.state)
      return self.state

    class Xswitch(MCgroup):
      """
      """
      def __init__(self, parent, name, active=True):
        self.name = name
        self.parent = parent
        self.logger = logging.getLogger(parent.logger.name+".Xswitch")
        self.state = self.get_state()

      def get_state(self):
        """
        Get the state from the hardware switch.

        The switch is sensed by bit 0 or 1 of the latch group at address 87
        Labjack 1. Low (value = 0) is for through and high is for crossed.

        Since latch group 1 also controls the IQ hybrids we need to read their
        states and make sure their bits remain the same.

        WBDC2 is different from WBDC1 in the use of the latchgroup bits.

        """
        self.logger.debug("get_state:  for %s", self)
        rx = self.parent.parent # WBDC_core instance which owns the latch group
        try:
          status = rx.lg['PLL'].read()
          self.logger.debug("get_state: Latch Group %s data = %s", rx.lg['PLL'],
                            Math.decimal_to_binary(status,8))
          test_bit_value = int(self.name)
          self.state = bool(status & test_bit_value)
          self.logger.debug("get_state: %s switch state = %d", self, self.state)
        except AttributeError, details:
          self.logger.error("WBDC_core.TransferSwitch.Xswitch.get_state: %s", details)
        return self.state

      def set_state(self, crossover=False):
        """
        Set the RF transfer (crossover) switch

        The switch is controlled by bits 0 and 1 of latch group 1 (address 80)
        of Labjack 1. Low (value = 0) is for crossed and high is for through.
        """
        self.logger.debug("set_state:  for %s", self)
        rx = self.parent.parent # WBDC_core instance which owns the latch group
        # get the current bit states
        try:
          status = rx.lg['X'].read()
          self.logger.debug("set_state: Latch Group %s data = %s", rx.lg['X'],
                            Math.decimal_to_binary(status,8))
        except AttributeError, details:
          self.logger.error("set_state: status read failed: %s", details)
          return False
        ctrl_bit = int(self.name)-1
        if crossover:
          value = Math.Bin.setbit(status, ctrl_bit)
        else:
          value = Math.Bin.clrbit(status, ctrl_bit)
        try:
          self.logger.debug("set_state: writing %s",
                            Math.decimal_to_binary(value,8))
          status = rx.lg['X'].write(value)
          if status:
            self.logger.debug("set_state: write succeeded")
          else:
            self.logger.error("set_state: write failed")
        except AttributeError, details:
          self.logger.error("set_state: write failed: %s", details)
          return False
        self.state = self.get_state()
        self.logger.debug("set_state: Xswitch state = %d", self.state)
        return self.state

  class PolSection(MCgroup):
    """
    Class for optional conversion of E,H pol tl L,R and attenuators adjustment.

    The attenuator assignment is as follows. R1 uses LJ 2,  R2 uses LJ3.
    The LJ port assignment is:::
      PolSec  Pol DAC  Pin  Port
      Rx-18    H   A    1   FIO0
               E   B    2   FIO1
      Rx-20    H   A    1   FIO2
               E   B    2   FIO3
      Rx-22    H   A    1   FIO4
               E   B    2   FIO5
      Rx-24    H   A    1   FIO6
               E   B    2   FIO7
      Rx-26    H   A    1   EIO0
               E   B    2   EIO1
    """
    def __init__(self, parent, name, active=True):
      """
      """
      MCgroup.__init__(self)
      self.logger = logging.getLogger(parent.logger.name+".PolSection")
      self.parent = parent
      self.name = name
      self.logger.debug(" initializing %s", self)
      chan = int(name[3:]) - 18 # I don't like taking this from the name
      # I don't like testing on the name but I can't think of a better way
      if re.search('R1', name):
          self.tdac = LJTickDAC(self.parent.LJ[2], self.name, IO_chan=chan)
      else:
          self.tdac = LJTickDAC(self.parent.LJ[3], self.name, IO_chan=chan)
      self.atten = {}
      for key in WBDC2hwif.pol_names:
        att_name = self.name+'-'+key
        self.atten[att_name] = self.IFattenuator(self, att_name)
        self.logger.debug("created attenuator %s", self.atten[att_name])

    def get_state(self):
      """
      Returns the state of the polarization conversion section.

      X,Y are converted to L,R if the state is 1.

      The pol section needs to know what band it belongs to to know what
      latches to use.  If that isn't available, return the default.
      """
      # Do this only if the subclass has been defined
      LGID = self.data['receiver']+'P'
      LGdata = self.parent.lg[LGID].read()
      self.logger.debug("get_state: LG %s returned %s", LGID,
                        Math.decimal_to_binary(LGdata,8))
      latchbit = (int(self.data['band'])-18)/2
      self.logger.debug("get_state: test bit is %d", latchbit)
      self.state = Math.Bin.getbit(LGdata,latchbit)
      self.logger.debug("get_state: state is %d", self.state)
      return self.state

    def set_state(self,state):
      """
      Sets the state of the polarization conversion section.

      If set, E,H are converted to L,R.

      The pol section needs to know what band it belongs to to know what
      latches to use.
      """
      # First get the current state of the latches
      LGID = self.data['receiver']+'P'
      latchbit = (int(self.data['band'])-18)/2
      LGdata = self.parent.lg[LGID].read()
      self.logger.debug("set_state: LG %s returned %s", LGID,
                        Math.decimal_to_binary(LGdata,8))
      # Now change the appropriate bit
      if state:
        newdata = Math.Bin.setbit(LGdata,latchbit)
      else:
        newdata = Math.Bin.clrbit(LGdata,latchbit)
      self.logger.debug("set_state: new data is %s",
                        Math.decimal_to_binary(newdata,8))
      # Write the new control word
      self.parent.lg[LGID].write(newdata)
      # Check it
      self.get_state()
      return self.state

    class IFattenuator(PINattenuator):
      """
      """
      def __init__(self, parent, name):
        """
        """
        self.parent = parent
        self.name = name
        mylogger = logging.getLogger(parent.logger.name+".IFattenuator")
        mylogger.debug("initializing %s with parent %s", self, self.parent)
        if re.search('E', name):
          vs = self.parent.tdac['A']
        else:
          vs = self.parent.tdac['B']
          
        if WBDC2hwif.splines[1][0].has_key(self.name):
          ctlV_spline =                WBDC2hwif.splines[1][0][self.name]
          min_gain, max_gain, ignore = WBDC2hwif.splines[1][1][self.name]
        else:
          ctlV_spline =                WBDC2hwif.splines_lab[1][0][self.name]
          min_gain, max_gain, ignore = WBDC2hwif.splines_lab[1][1][self.name]
        PINattenuator.__init__(self, parent, name, vs, ctlV_spline,
                               min_gain, max_gain)
        self.logger = mylogger

  class DownConv(MCgroup):
    """
    Converts RF to IF

    A hybrid optional converts the I and Q IFs to LSB and USB.
    """
    def __init__(self, parent, name, active=True):
      """
      """
      MCgroup.__init__(self)
      self.logger = logging.getLogger(parent.logger.name+".DownConv")
      self.name = name
      self.parent = parent
      self.state = self.get_state()
      self.logger.debug(" %s IF mode is %s", self, self.state)

    def _get_latch_info(self):
      """
      """
      self.logger.debug("_get_latch_info: called for pol %s, band %s, rx %s",
                        self.data['pol'],
                        self.data['band'],
                        self.data['receiver'])
      polno = int(self.data['pol'][-1])-1
      self.logger.debug("_get_latch_info: pol number %d", polno)
      if int(self.data['band']) < 21:
        LGID = self.data['receiver']+'I1'
        latchbit = int(self.data['band']) - 18 + polno
      else:
        LGID = self.data['receiver']+'I2'
        latchbit = int(self.data['band']) - 22 + polno
      self.logger.debug("_get_latch_info: latch bit %d on group %s selected",
                        latchbit, LGID)
      return LGID, latchbit

    def get_state(self):
      """
      """
      if self.data.has_key('receiver'):
        LGID, latchbit = self._get_latch_info()
        try:
          latchdata = self.parent.lg[LGID].read()
        except Exception, details:
          self.logger.error("_get_state: read failed: %s", str(details))
        self.state = Math.Bin.getbit(latchdata, latchbit)
      else:
        self.state = False
      return self.state

    def set_state(self, state):
      """
      """
      if self.data.has_key('receiver'):
        LGID, latchbit = self._get_latch_info()
        latchdata = self.parent.lg[LGID].read()
        self.logger.debug("_set_state: latchdata was %s",
                          Math.decimal_to_binary(latchdata,8))
        if state:
          latchdata = Math.Bin.setbit(latchdata, latchbit)
        else:
          latchdata = Math.Bin.clrbit(latchdata, latchbit)
        self.logger.debug("_set_state: latchdata is %s",
                          Math.decimal_to_binary(latchdata,8))
        try:
          self.parent.lg[LGID].write(latchdata)
        except Exception, details:
          self.logger.error("_set_state: write failed: %s", str(details))
      self.get_state()
      return self.state

  class AnalogMonitor(MCobject):
    """
    """
    def __init__(self, parent, mon_points):
      """
      """
      self.parent=parent
      self.logger = logging.getLogger(self.parent.logger.name+".AnalogMonitor")

    def read_analogs(self, latchgroup=1):
      """
      """
      self.logger.debug("read_analogs: latch group=%d", latchgroup)
      latchAddress = latchgroup - 1
      self.logger.debug("read_analogs: latch address=%d", latchAddress)
      LGname = 'A'+str(latchgroup)
      self.logger.debug("read_analogs: latch name=%s", LGname)
      mon_data = WBDC2hwif.mon_points[latchgroup]
      mon_pts = mon_data.keys()
      mon_pts.sort()
      self.logger.debug("read_analogs: monitor points: %s", mon_pts)
      analog_data = {}
      for point in mon_pts:
        mon_pt_addr = mon_data[point][0]
        self.logger.debug("read_analogs: sending %d", mon_pt_addr)
        self.parent.lg[LGname].write(mon_pt_addr)
        for dataset in [0,1]:
          self.logger.debug('read_analogs: dataset=%d',dataset)
          label =  mon_data[point][dataset+1].strip()
          self.logger.debug('read_analogs: reading %s', label)
          AINnum = latchAddress*2+dataset
          # in the next line, LGname can be A1 or A2
          self.logger.debug("read_analogs: reading AIN%d", AINnum)
          analog_data[label] = self.parent.lg[LGname].LJ.getAIN(AINnum)
          self.logger.debug("read_analogs: read %f", analog_data[label])
      return analog_data

    def get_monitor_data(self, latchgroup=1):
      """
      """
      monitor_data = {}
      analog_data = self.read_analogs(latchgroup)
      for ID in analog_data.keys():
        if ID:
          monitor_data[ID] = self.convert_analog(ID, analog_data[ID])
      return monitor_data

    def convert_analog(self, ID, value):
      """
      This works in conjunction with the monitor point keys
      """
      self.logger.debug("convert_analog: called for %s for %f", ID, value)
      if ID == '+6 V dig':
        return value*4.0211
      elif ID == '+6 V ana':
        return value*4.0278
      elif ID == '+16 V':
        return value*10.5446
      elif ID == '+12 V':
        return value*10.5827
      elif ID == '-16 V':
        return value*-10.5446
      elif re.search(' V ', ID):
        # This must be a current
        return value-0.026
      elif re.search('plane', ID):
        # This must be RF power
        return (value-0.004)*2.0064
      elif re.search('plate', ID):
        # This must be a temperature
        return (value+0.2389275)*23.549481
      else:
        self.logger.error("convert_analogs: unknown ID: %s", ID)

       
  # ------------------------------- WBDC2hwif methods -------------------------

  def has_labjack(self, localID):
    """
    """
    if self.LJ.has_key(localID):
      return True
    else:
      self.logger.error(" %s has no LabJack %d", self.name, localID)
      return False

  def configure_MB_labjack(self):
    """
    Configure LabJack 1 for digital module control and analog monitoring
    """
    if self.has_labjack(1):
      # Analog input for voltages, currents and temperatures
      FIOanalog = int('00001111',2)
      self.LJ[1].configIO(FIOAnalog=FIOanalog,EIOAnalog=0)
      CIOBitDir = int('1111',2)
      EIOBitDir = int('11111111',2)
      FIOBitDir = int('00000000',2)
      direction = [FIOBitDir, EIOBitDir, CIOBitDir]
      mask = [0xff,0xff,0xff]
      self.logger.debug("LabJack %d direction=%s, write mask=%s",
                        self.LJ[1].localID, direction, mask)
      try:
        status = self.LJ[1].getFeedback(u3.PortDirWrite(Direction=direction,
                                                        WriteMask=mask))
        self.logger.debug(" configure status: %s", status)
      except Exception, details:
        self.logger.error(" Could not set bit direction on U3 %d",
                          self.LJ[1].localID)
        raise ObservatoryError("","configuring LJ 1 failed:\n"+str(details))
    else:
      raise ObservatoryError("","LabJack 1 is not connected")

  def configure_atten_labjack(self, ID):
    """
    Configure a LabJack for PIN diode attenuator control
    """
    if self.has_labjack(ID):
      self.LJ[ID].configIO(EIOAnalog=0, FIOAnalog=0)
      CIOBitDir = int('0000',2)
      EIOBitDir = int('00000000',2)
      FIOBitDir = int('00000000',2)
      direction = [FIOBitDir, EIOBitDir, CIOBitDir]
      mask = [0xff,0xff,0xff]
      self.logger.debug(" LabJack %d direction=%s, write mask=%s",
                        ID, direction, mask)
      try:
        status = self.LJ[ID].getFeedback(u3.PortDirWrite(Direction=direction,
                                                         WriteMask=mask))
        self.logger.debug(" configure status: %s", status)
      except Exception, details:
        self.logger.error(" Could not set bit direction on U3 %d",
                          self.LJ[ID].localID)
        raise ObservatoryError("LabJack "+str(ID),
                               "not configured:\n"+str(details))
    else:
      raise ObservatoryError("LabJack "+str(ID)," is not connected")

