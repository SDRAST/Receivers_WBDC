"""
Module to provide class WBDC_core

Monitor and Control
===================

For a description of the generic Wide Band Down Converter see/do
MonitorControl.Receivers.WBDC.__doc__.split('\n')

Monitor and control is done with two or three LabJacks. For a detailed
description of the LabJack see/do
MonitorControl.Electronics.Interfaces.LabJack.__doc__.split('\n')

The LabJack with local ID 1 controls and reads switches, and reads analog
data (currents, voltages, temperatures). LabJack 2 (and 3 for WBDC2) control
attenuators using TickDACs to provide analog control voltages.

LabJack 1
=========

This LabJack is capable of addressing 256 X 8 bit latches. They are grouped in
sets of 8 latches. The first four of the latch groups (i.e. 0-3, 8-11, 16-19,
..., 80-83, ..., 248-251) are write to control bits. The second four of the
latch groups (i.e. 4-7, 12-15, 20-23, ...,84-87, ..., 252-255) are read bits
for status (i.e.  switch position indicators). A0-A7 is used to address a
specific 8 bit latch for writing or reading. The latch data are sent or read
serially, MSB first.  The bit address assignment differs for WBDC1 and WBDC2
and are described with those classes.

The digital board LabJack maps to the board's signals as follows::
      ---Labjack---  -----------WBDC----------------------------------
      Name  Channel  Name       Function
      FI00     0     CH0 IMON   Analog input measuring supply currents
      FIO1     1     CH1 VMON   Analog Input measuring supply voltages
      FIO2     2     CH3 TEMP   Analog input measuring temperatures
      FI03     3     CH4 LNA    not used
      FI04     4
      FI05     5
      FI06     6
      FI07     7     SDO        Digital input from readback

      EI00     8     A0         Latch address LSB
      EI01     9     A1         ..
      Ei02    10     A2         ..
      EI03    11     A3         ..
      EI04    12     A4         ..
      EI05    13     A5         ..
      EI06    14     A6         ..
      EI07    15     A7         Latch address MSB

      CI00    16     SCK        Serial Clock input
      CI01    17     SDI        Data input
      CI02    18     NLOAD      Load data to/from latches
      CI03    19     CS-BUS     Eable writing to or reading from latch

The state of NLOAD is normallly high. When checking status (or reading bits), toggle NLOAD low for at least 10 mS then high to store the information for reading.

CS-BUS is the global enable. The normal state is high. Set to this to low when programming latches or reading data. Then set high when done.

Control
-------

The switches are controlled by digital latches (logical devices which
preserve a specified logic state). The latches are connected to serial-in
parallel-out registers.  These registers are addressed using the EIO
out bits of LabJack 1.  The data are then clocked into the register using
the SDI and SCK signals.

The latch groups may be designated by their circuit name (LATCH1 and LATCH2)
or their address (80 or 81).

Latch Group 1 (Address 80)
~~~~~~~~~~~~~~~~~~~~~~~~~~
The feed switch pair is controlled by bit L1A0 (A0 on Latch 1)::
  0 for through
  1 for crossed-over
The receiver 1 polarizer is controlled by L1A1 and L1A2::
  01 for linear
  10 for circular
The receiver 2 polarizer is controlled by L1A3 and L1A4 with the same logic.

L1A5 controls the PLO switch::
  0 for 22 FHz
  1 for 24 GHz

Latch Group 2 (Address 81)
~~~~~~~~~~~~~~~~~~~~~~~~~~
The I/Q to U/L converters are controlled by L2A0 through L2A7.  Each
bit pair handles one converter.  So L2A0 and L2A1 control receiver 1
pol 1 with this logic::
  01 for I/Q
  10 for U/L
and the same for the other four.

Monitoring
----------

Three latch groups are assigned to digital monitoring, that is, the program
reads the latch states.

Latch Group 2 (Address 82)
~~~~~~~~~~~~~~~~~~~~~~~~~~
Latch group 2 (L2A0 - L2A7) has a read address of 85. The switches directing
signals to/from or around the I/Q->U/L hybrids have no tell-tales, so one
simply reads the states of the control signals.


Latch group 3
~~~~~~~~~~~~~
The polarization switches have tell-tales and are read by latch group 3
with an address of 86.  These switches are controlled in pairs but read
individually. So whereas Receiver 1's polarizer is commanded with
latches L1A1 and L1A2, the switches states are given by L3A0 thru L3A3.
The mapping is weird.  The state of L1A1 is reflected by L3A0 and L3A3,
whereas the state of L1A2 is reflected by L3A1 and L3A2.

Latch group 4
~~~~~~~~~~~~~
has address 87. L4A0 and L4A1 are used monitor the receiver select switches,
which are controlled with one signal, L1A0

L4A4 monitors the state of the PLO switch.

L4A2 monitors the 22 GHz PLO lock and L4A3 the 24 GHz PLO lock

Latch LEDs
~~~~~~~~~~
The monitor bits should match the LEDs to the top right of the motherboard.
With the hinge of the lid at the bottom the LEDs are in LSB -> MSB order
and grouped as::
  LATCH86 LATCH87
  LATCH84 LATCH85
If the box is mounted on a wall or ceiling and the lid is hanging down,
the order is more conventional.

Latch Addresses 0 and 2
~~~~~~~~~~~~~~~~~~~~~~~
There are a number of registers used to select analog monitoring points.
An bit pattern sent to latch address 0 selects a current and a voltage
to be connected to AIN0 and AIN1.  A bit pattern sent to latch address
2 selects a thermistor to be connected to AIN2.  AIN3 is not used in this
receiver.

Attenuators
-----------

There are four RF voltage-controlled attenuators (PIN diodes) for each
down-converter sub-band.  The four voltages are generated in LabJack
TickDACs attached to LabJack2 (and 3 for WBDC2).

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

LabJack 2 (and 3)
-----------------

Typical Configuration
---------------------
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

import Math
import MonitorControl
from MonitorControl import ObservatoryError
from MonitorControl.Receivers.WBDC import WBDC_base
from Electronics.Interfaces.LabJack import connect_to_U3s, LJTickDAC

from support import python_version

# These map the WBDC signal names into the LabJack digital IO lines.
WBDCsignal = {
  'IMON':0, 'VMON':1, 'TEMP':2, 'LNA':3, 'SDO':7,
  'A0':8, 'A1':9, 'A2':10, 'A3':11, 'A4':12, 'A5':13, 'A6':14, 'A7':15,
  'SCK':16, 'SDI':17, 'NLOAD':18, 'CS-BUS':19}

module_logger = logging.getLogger(__name__)

class WBDC_core(WBDC_base):
  """
  A class to provide the generic WBDC monitor and control functionality.

  It implements most of the methods originally in the {\tt WBDC_1} module as
  class methods. The addresses of the monitor and control points are likely to
  be different for the two WBDC implementations so these must be provided in
  dictionaries in the appropriate sub-classes.
  """
  def __init__(self, name, inputs = None, output_names=None, active=True):
    """
    Initialize a physical WBDC object.

    At least one Signal instance must be specified for inputs.

    @param name : unique identifier
    @type  name : str

    @param inputs : a dict with sources for different inputs
    @type  inputs : dict of str:str

    @param output_names : names of the output channels/ports
    @type  output_names : list of str

    @param active : True is the FrontEnd instance is functional
    @type  active : bool
    """
    WBDC_base.__init__(self, name, active=active, inputs=inputs,
                      output_names=output_names)
    self.logger = logging.getLogger(module_logger.name+".WBDC_core")
    self.logger.debug(" WBDC_core initializing %s", self)
    self.logger.info(" %s inputs: %s", self, str(self.inputs))
    self.find_labjacks()
    self.verify_labjacks()

  def find_labjacks(self):
    """
    Find the LabJacks for this WBDC

    WBDC1 has two LabJacks numbered 1 and 2.  WBDC has three LabJacks.
    LabJack 1 is the motherboard controller.  LabJacks 2 and 3 control the PIN
    diode attenuators.

    WBDC1 has a LabJack 3 which is the front-end controller.
    """
    self.logger.info("find_labjacks: entered")
    self.LJ = connect_to_U3s()
    self.logger.info("find_labjacks: found %s", self.LJ.keys())
    return self.LJ.keys()

  def has_labjack(self, localID):
    """
    """
    if self.LJ.has_key(localID):
      return True
    else:
      self.logger.error(" %s has no LabJack %d", self.name, localID)
      return False
      
  def verify_labjacks(self):
    """
    """
    # Is there a motherboard controller?
    if self.has_labjack(1):
      # A MB controller has F bits 0-3 set for analog input
      if self.LJ[1].configIO()['FIOAnalog'] != 15:
        self.logger.info("Configuring LabJack 1 for MB control")
        self.configure_MB_labjack()
    else:
      raise ObservatoryError("","LabJack 1 is not connected")
    if self.has_labjack(2):
      # A LJ with a TickDAC mounted on an FIO section has that section
      # configured for digital output.  
      if self.LJ[2].configU3()['EIOState']!= 255:
        self.logger.info("Configuring LabJack 2 for attenuator control")
        self.configure_atten_labjack(2)
    else:
      raise ObservatoryError("","LabJack 2 is not connected")
    if self.name == 'WBDC-2' and self.has_labjack(3):
      if self.LJ[3].configU3()['EIOState']!= 255:
        self.logger.info("Configuring LabJack 3 for attenuator control")
        self.configure_atten_labjack(3)
    else:
      raise ObservatoryError("","LabJack 3 is not connected")

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
      self.logger.info("LabJack %d direction=%s, write mask=%s",
                        self.LJ[1].localID, direction, mask)
      try:
        status = self.LJ[1].getFeedback(u3.PortDirWrite(Direction=direction,
                                                        WriteMask=mask))
        self.logger.info(" configure status: %s", status)
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
        self.logger.info(" configure status: %s", status)
      except Exception, details:
        self.logger.error(" Could not set bit direction on U3 %d",
                          self.LJ[ID].localID)
        raise ObservatoryError("LabJack "+str(ID),
                               "not configured:\n"+str(details))
    else:
      raise ObservatoryError("LabJack "+str(ID)," is not connected")
      
  def set_signals(self, signal_dict):
    """
    Sets signals for programming and reading data.

    The signals are provided as a dictionary with the keys as signal names
    defined in WBDCsignal.  For example:

    >>> set_signals(LJ,{"SCK":1, "SDA":1,"NLOAD":1, "CS-BUS":1})

    Invoked with an empty dictionary it returns the state of the digital
    I/O ports:

    In [3]: set_signals(lj[1],{})
    Out[3]: [{'CIO': 15, 'EIO': 86, 'FIO': 240}]

    To give the signals time to settle, a 10 ms wait is included.  Until
    Python 2.6, time.sleep() must be used.

    @type LJ : u3.U3 class instance
    @param LJ : LabJack to be accessed

    @type signal_dict : dictionary
    @param signal_dict : signal names and states

    @return: result of u3.BitStateWrite()
    """
    commands = []
    for signal,state in signal_dict.items():
      commands.append(u3.BitStateWrite(WBDCsignal[signal], state))
    commands.append(u3.PortStateRead())
    self.logger.debug("set_signals: sending %s", commands)
    try:
      result = self.LJ[1].getFeedback(commands)
      self.logger.debug("set_signals: command feedback: %s", result)
      if float(python_version()[:3]) < 2.6:
        time.sleep(0.01)
    except Exception, details:
      self.logger.error("set_signals: LJ commands failed:\n%s", details)
    return result[-1]

  class TransferSwitch(WBDC_base.TransferSwitch):
    """
    Beam to down-converter transfer switch

    There is one Switch object for each front-end polarization P1 and P2.

    At some point this might become a general transfer switch class
    """
    def __init__(self, parent, name, inputs=None, output_names=None):
      self.name = name
      mylogger = logging.getLogger(module_logger.name+".TransferSwitch")
      mylogger.debug(" initializing %s", self)
      mylogger.debug(" %s inputs: %s", self, str(inputs))
      WBDC_base.TransferSwitch.__init__(self, parent, name, inputs=inputs,
                                        output_names=output_names)
      self.logger = mylogger
      mylogger.debug(" %s inputs: %s", self, str(inputs))
      self.parent = parent

    def get_subswitch_state(self, ID):
      """
      This gets the state from the hardware.

      This method must be equated to the Switch object method _get_state
      """
      subswitch = self.data[ID]
      self.logger.debug(" getting state for %s", subswitch)
      devID = subswitch.name
      rx = subswitch.parent.parent
      lg1 = lg = LatchGroup(parent=rx, address=87)
      status = lg1.read()
      self.logger.debug(" Latch Group 1 data = %s",
                        Math.decimal_to_binary(status,8))
      test_bit = int(devID[-1])
      subswitch.state = status & test_bit
      self.logger.debug(" switch state = %d", subswitch.state)
      return subswitch.state

  class RFsection(WBDC_base.RFsection):
    """
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      self.parent = parent
      WBDC_base.RFsection.__init__(self, parent, name, inputs=inputs,
                                  output_names=output_names, active=True)
      self.logger = logging.getLogger(module_logger.name+".RFsection")
      self.logger.debug(" initializing WBDC_core %s", self)
      self.logger.info(" %s inputs: %s", self, str(self.inputs))
      self.logger.info("%s outputs: %s", self, str(self.outputs))

  class PolSection(WBDC_base.PolSection):
    """
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      WBDC_base.PolSection.__init__(self, parent, name, inputs=inputs,
                                  output_names=output_names,
                                  active=active)
      self.logger = logging.getLogger(module_logger.name+".PolSection")
      self.logger.debug(" __init__: output names: %s",
                        output_names)
      self.logger.debug(" initializing WBDC_core %s", self)
      self.logger.info(" %s inputs: %s", self, str(self.inputs))
      self.logger.info(" %s outputs: %s", self, str(self.outputs))

    def get_pol_mode(self):
      self.logger.debug("(core) get_pol_mode: invoked")
      mode = super(WBDC_core.PolSection,self).get_pol_mode()
      return mode

    def _get_pol_mode(self):
      self.logger.debug("(core) _get_pol_mode: invoked")
      return None

  class DownConv(WBDC_base.DownConv):
    """
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      WBDC_base.DownConv.__init__(self, parent, name, inputs=inputs,
                                 output_names=output_names,
                                 active=active)
      self.logger = logging.getLogger(module_logger.name+".DownConv")
    
class LatchGroup():
  """
  Class for a group of eight WBDC latches

  Each WBDC digital module has four groups of eight latches.  The groups are
  numbered 1-4.  Each group has a write address and a read address::
           DM1         DM2
        write read  write read
    LG1   80   84    160   164
    LG2   81   85    161   165
    LG3   82   86    162   166
    LG4   83   87    163   167

    The latch groups are controlled by LabJack1.
  """
  def __init__(self, parent=None, address=None):
    """
    Creates a LatchGroup instance
    
    @type LJ : u3.U3 class instance
    @param LJ : LabJack controlling the latch

    @type address : int
    @param address : latch address
    """
    self.logger = logging.getLogger(__name__+".LatchGroup")
    if parent == None:
      self.logger.error("%s must have a parent", self)
      raise ObservatoryError(":", " no receiver specified")
    else:
      self.parent = parent
    if address == None:
      self.logger.error("%s must have an address", self)
      raise ObservatoryError(":", "no address")
    else:
      self.address = address

  def setLatchAddr(self):
    """
    select a latch by address

    @type LJ : u3.U3 class instance
    @param LJ : LabJack which controls the latches

    @type LATCHNUM : int
    @param LATCHNUM : number of latch to be addressed

    @return: boolean
    """
    states = [0,self.address,0]
    mask = [0,0xff,0] # EIO port
    self.logger.debug("setLatchAddr: writing %s to bits %s to select latch %s",
                      states, mask, self.address)
    try:
      self.parent.LJ[1].getFeedback(
                           u3.PortStateWrite(State = states, WriteMask = mask))
      return True
    except u3.LabJackException, details:
      self.logger.error("setLatchAddr: LabJack could not set latch %d\n%s",
                        self.addr, str(details))
      return False

  def read(self):
    """
    read the bit pattern at a latch

    @return: byte
    """
    self.logger.debug("read: Reading latch %d", self.address)
    # Select the latch to be read
    if self.setLatchAddr():
      port_states = self.parent.LJ[1].getFeedback(u3.PortStateRead())
      self.logger.debug("read: port states: %s", port_states)
      latchAddr = port_states[0]['EIO']
      self.logger.debug("read: LatchGroup address is %d",latchAddr)
      if latchAddr != self.address:
        self.logger.debug("read: Requested latch %d but got %d",
                          seld.address, latchAddr)
        return None
      else:
        self.logger.debug("read: latch address set to %d", self.address)
        portStates = self.parent.set_signals(
                                 {"SCK":1, "SDI":1,"NLOAD":1, "CS-BUS":1})
        # Store the information to be read from this address
        self.parent.set_signals({"NLOAD":0})
        self.parent.set_signals({"NLOAD":1})
        # Enable serial data transfer
        self.parent.set_signals({"CS-BUS":0})
        MBDATA = 0
        # Process from MS to LS bit
        for bit in range(7,-1,-1):
          try:
            state = self.parent.LJ[1].getFeedback(
                            u3.BitStateRead(IONumber = WBDCsignal["SDO"]))[0]
            self.logger.debug("read: bit %d state is %d for MBDATA = %d",
                              bit, state, MBDATA)
          except Exception, details:
            self.logger.error("read: Data In failed at bit %d\n%s",
                              bit, details)
            return None
          if state:
            MBDATA = Math.Bin.setbit(MBDATA, bit)
          if bit > 0:
            self.parent.set_signals({"SCK":0})
            self.parent.set_signals({"SCK":1})
          self.parent.set_signals({"CS-BUS":1})
          return MBDATA
    else:
      self.logger.error("read: Setting latch address failed")
      return -1

class Attenuator(LJTickDAC):
  """
  Voltage-controlled PIN diode attenuator for WBDC

  @type bias_list : list of float
  @ivar bias_list : bias voltages for calibration

  @type volts : list of float
  @ivar volts : auto-generated control voltages for calibration (V)

  @type pwrs : list of float
  @ivar pwrs : measured powers corresponding to 'volts' (dBm)

  @type bias : float
  @ivar bias : best bias value out of 'bias_list'

  @type coefs : numpy array of float
  @ivar coefs : polynomial coeffients for best calibration curve

  @type lower : float
  @ivar lower : lowest power measured

  @type upper : float
  @ivar upper : highest power measured

  @type atten_table : dictionary
  @ivar atten_table : control voltage indexed by attenuation
  """
  def __init__(self,LabJack,pin):
    """
    """
    LJTickDAC.__init__(self,LabJack,pin)
    print "Initializing attenuator on LabJack",LabJack.localID
    self.pwrs = {}
    self.bias = 3.0
    # The IDs match the WBDC receiver channels
    if pin == 0:
      self.ID = 1
      self.coefs = NP.array([2.24305829e-03,  3.47608278e-02,
                             1.91564653e-01,  3.57628078e-01,
                            -4.44852926e-01, -2.43563471e+00,
                            -4.14345128,     -8.16101008])
      self.lower = -5.0
      self.upper =  1.75
    elif pin == 2:
      self.ID = 2
      self.coefs = NP.array([1.97246882e-03,  3.15527700e-02,
                             1.80115477e-01,  3.54211343e-01,
                            -3.82845997e-01, -2.30612599,
                            -4.14205717,     -8.34552823    ])
      self.lower = -5.0
      self.upper =  1.75
    elif pin == 4:
      self.ID = 3
      self.coefs = NP.array([2.06521060e-03,  3.27308482e-02,
                             1.84436385e-01,  3.52212701e-01,
                            -4.20502519e-01,  -2.32719384,
                            -4.05112656,      -8.39222065   ])
      self.lower = -5.0
      self.upper =  1.75
    elif pin == 6:
      if LabJack.localID == 2:
        self.ID = 4
        self.coefs = NP.array([2.13996316e-03,  3.34458388e-02,
                               1.85709249e-01,  3.46131441e-01,
                              -4.43162863e-01, -2.31329518,
                              -3.91949192,     -8.55680332])
        self.lower = -5.0
        self.upper =  1.75
      elif LabJack.localID == 3:
        self.ID = 5
        self.coefs = NP.array([-1.11465757e-04, -9.83309141e-04,
                                1.73887763e-03,  2.92728140e-02,
                                3.68747270e-02, -4.86525897e-02,
                               -4.63506048e-01,  -2.74735018])
        self.lower = -6.0
        self.upper =  1.75
    else:
      self.ID = None
    self.volts = [self.lower,self.upper]

  def set_default(self):
    """
    This sets all attenuators to 5 dB, based on a previous
    calibration.
    """
    if self.ID == 1:
      self.setVoltages([3.0,-0.370])
    elif self.ID == 2:
      self.setVoltages([3.0,-0.539])
    elif self.ID == 3:
      self.setVoltages([3.0,-0.490])
    elif self.ID == 4:
      self.setVoltages([3.0,-0.724])
    elif self.ID == 5:
      self.setVoltages([3.0,-0.5])

  def get_calibration_data(self, pm,
                           limits=None,
                           bias=None,
                           save=True,
                           filename=None,
                           show_progress=False):
    """
    Obtains measured power as a function of control voltage

    This gets the data needed to calibrate a PIN diode attenuator
    between 'limits' ( = (lower,upper) ) control voltages.
    'bias' is an optional list of bias voltages.

    Generates these public attributes:
      - self.bias_list
      - self.volts
      - self.pwrs

    @type pm : Gpib.Gpib instance
    @param pm : power meter for the power readings

    @type limits : tuple of float
    @param limits : (lower test voltage, upper test voltage). If limits
    is not provided, (-5,1.75) will be used.

    @type bias : list of float
    @param bias : bias voltages for the PIN diode. ints are acceptable.
    If bias is not a list but a number it will be converted to a list.
    So far, the diodes tested have a best bias of 3.0 V.

    @type save : bool
    @param save : True to save data to a file

    @type filename : str
    @param filename : name of text file for data.  If it is not provided
    the data will not be saved.  If it is "", the file will be in the
    current directory with a default name

    @return: dictionary of control voltage lists, dictionary of measured
    powers, both indexed by bias voltage, and a list of biases.
    """
    pwrs = {}
    if bias == None:
      self.bias_list = [2, 2.5, 3, 3.5, 4]
    elif type(bias) == float or type(bias) == int:
      self.bias_list = [bias]
    else:
      self.bias_list = bias
    if limits == None:
      minV, maxV = -5, 1.75
    else:
      # arrange for 0.25 V steps
      minV = round(limits[0]*4)/4.
      maxV = round(limits[1]*4)/4.
    num_steps = int((maxV - minV)/.25)+1
    self.volts = NP.linspace(minV,maxV,num_steps)
    for bias in self.bias_list:
      if show_progress:
        print "Doing bias of",bias,"V",
      self.pwrs[bias] = []
      for volt in self.volts:
        self.setVoltages([bias,volt])
        if show_progress:
          print ".",
          sys.stdout.flush()
        # Give the power meter time to range and settle
        time.sleep(1)
        self.pwrs[bias].append(float(pm.read().strip()))
      if show_progress:
        print

    text = "# Attenuator "+str(self.ID)+"\n"
    text += "# Biases: "+str(self.bias_list)+"\n"
    for index in range(len(self.volts)):
      text += ("%5.2f " % self.volts[index])
      for bias in self.bias_list:
        text += ("  %7.3f" % self.pwrs[bias][index])+"\n"
    if filename != None:
      if filename:
        datafile = open(filename,"w")
      else:
        datafile = open("atten-"+str(self.ID)+".txt","w")
      datafile.write(text)
      datafile.close()
    return text

  def controlVoltage(self,pwr):
    """
    Compute control voltage for a given attenuation

    @return: float control voltage V
    """
    function = scipy.poly1d(self.coefs)
    minV = self.volts[0]
    maxV = self.volts[-1]
    return scipy.optimize.bisect(function-pwr,minV,maxV)

  def set_atten(self,atten):
    """
    Set the attenuation


    """
    if atten > 0.0:
      atten *= -1.
    if atten > 15:
      raise "Too much attenuation requested"
    else:
      volt = self.controlVoltage(atten)
      self.setVoltages([self.bias,volt])

  def useful_range(self,polycoefs):
    """
    Report minimum and maximum measurable attenuation.

    @type polycoefs : numpy array of float
    @param polycoefs : polynomial coefficients
    """
    function = scipy.poly1d(polycoefs)
    return Math.ceil(function(self.volts[-1])*10)/10, \
           Math.floor(function(self.volts[0])*10)/10

  def atten(self,polycoefs,controlV):
    """
    @type polycoefs : numpy array of float
    @param polycoefs : polynomial coefficients

    @type controlV : float
    @param controlV : control voltage (V)
    """
    return function - scipy.poly1d(polycoefs)(controlV)

  def fit_calibration_data(self):
    """
    Fit the power vs voltage curves taken with self.get_calibration_data().

    Generates these public attributes:
      - bias
      - coefs
      - lower
      - upper
      - atten_table
    """
    pwr_range = 0
    for bias in self.bias_list:
      polycoefs = scipy.polyfit(self.volts, self.pwrs[bias], 7)
      yfit = scipy.polyval(polycoefs,self.volts)
      lower,upper = self.useful_range(polycoefs)
      if (upper-lower) > pwr_range:
        pwr_range = upper-lower
        best_coefs = polycoefs
        self.coefs = scipy.polyfit(self.volts,
                                   NP.array(self.pwrs[bias])-upper,
                                   7)
        best_lower, best_upper = lower, upper
        self.bias = self.bias_list
    if pwr_range:
      # self.bias should now have the best bias (if there was more than
      # one to try, and a set of polynomial coefficients
      self.lower = best_lower
      self.upper = best_upper
      self.atten_table = {}
      for pwr in NP.arange(self.lower,self.upper,1):
        ctrlVolts = self.controlVoltage(pwr-self.upper)
        self.atten_table[self.upper-pwr] = ctrlVolts
      self.atten_table[0] = self.controlVoltage(0)
      return True
    else:
      return False

def get_pol_section_state(device):
  devID = device.name
  module_logger.debug(" getting polarization state for %s", devID)
  return False
