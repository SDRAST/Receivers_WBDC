"""
LabJack 1 is capable of addressing 256 X 8 bit latches on a WBDC motherboard.
They are grouped in sets of 8 latches. The first four of the latch groups::
  (0-3, 8-11, 16-19, ..., 80-83, ..., 248-251)
are write-to control bits. The second four of the latch groups::
  (4-7, 12-15, 20-23, ...,84-87, ..., 252-255)
are read bits for status (i.e. switch position indicators).

A0-A7 (also known as EIO0-EIO7) are used to address a specific 8 bit latch for
writing or reading. The latch data are sent or read serially, MSB first.
The latch group address encoded with the EIO bits consists of three parts::
  EIO7-EIO3 encodes the digital module (DM) address.
  EIO2      indicates write if 0 and read if 1.
  EIO1-EIO0 selects the latch group (LG) in a digital module.
So latches in write-mode have addresses ending in 0~3.  Latches in read-mode
have addresses ending in 4~7.  For example,DM~1 LG~1 has a EIO value (address)
of 80 (0101~0000) in WBDC1 and 8 (0000~1000) in WBDC2. LG~2 in any DM has
EIO0=1.  DM~2 LG~1 has address 16 in WBDC2. (WBDC1 has no DM~2.)

Operation of the LabJack is described in
/usr/local/lib/python2.7/DSN-Sci-packages/Electronics/Interfaces/LabJack/\
    labjack_u3_users_guide.pdf

The bit address assignment differs for WBDC1 and WBDC2 and are described with
those classes.

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

The state of NLOAD is normallly high. When checking status (or reading bits),
toggle NLOAD low for at least 10 mS then high to store the information for
reading.

CS-BUS is the global enable. The normal state is high. Set to this to low when
programming latches or reading data. Then set high when done.

Latch LEDs
~~~~~~~~~~
The monitor bits should match the LEDs in the digital module(s) near the top of
the motherboard (right on WBDC1, left on WBDC2) with the hinge of the lid at the
bottom.  The LEDs are in LSB -> MSB order and grouped as::
  LATCH86 LATCH87       LATCH166 LATCH167
  LATCH84 LATCH85       LATCH164 LATCH165
In this orientation, the LED rows read backwards.  If the box is mounted on a
wall or ceiling and the lid is hanging down, the order is more conventional.

Latch Addresses 0 and 2
~~~~~~~~~~~~~~~~~~~~~~~
There are a number of registers used to select analog monitoring points.
bit pattern sent to latch address 0 selects a current and a voltage
to be connected to AIN0 and AIN1.  A bit pattern sent to latch address
2 selects a thermistor to be connected to AIN2.  AIN3 is not used in this
receiver.
"""
import u3
import logging
import time

import Math
from Math.Bin import getbit
from support import python_version
from MonitorControl import ObservatoryError

module_logger = logging.getLogger(__name__)

# These map the WBDC signal names into the LabJack digital IO lines.
WBDCsignal = {
  'IMON':0, 'VMON':1, 'TEMP':2, 'LNA':3, 'SDO':7,
  'A0':8, 'A1':9, 'A2':10, 'A3':11, 'A4':12, 'A5':13, 'A6':14, 'A7':15,
  'SCK':16, 'SDI':17, 'NLOAD':18, 'CS-BUS':19}


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
  def __init__(self, parent=None, labjack=None, DM=1, LG=None):
    """
    Creates a LatchGroup instance

    @param parent : device to which the LatchGroup instance belongs
    @type  parent : Device subclass instance

    @type  labjack : u3.U3 class instance
    @param labjack : LabJack controlling the latch

    @param DM : digital module number
    @type  DM : int

    @param LG : latch group number
    @type  LG : int
    """
    mylogger = logging.getLogger(__name__+".LatchGroup")
    if parent == None and labjack == None:
      mylogger.error("%s must have a labjack or a parent with a labjack", self)
      raise ObservatoryError(":", " no labjack or receiver specified")
    elif labjack == None:
      self.parent = parent
      self.LJ = self.parent.LJ[1] # LabJack 1 is always the DM controller
    else:
      self.LJ = labjack
    if DM == None or LG == None:
      mylogger.error("%s must have digital module and latch group codes", self)
      raise ObservatoryError(":", "no latch group")
    else:
      self.address = self.getLatchAddr(parent, DM=DM, LG=LG)
    self.name = str(self.address)
    self.logger = mylogger
    self.setLatchAddr()

  def getLatchAddr(self, parent=None, DM=1, LG=1, read=False):
    """
    Returns the address for the given latch group

    @param parent : device to which the LatchGroup instance belongs
    @type  parent : Device subclass instance

    @param DM : digital module number
    @type  DM : int

    @param LG : latch group number
    @type  LG : int

    @param read : latch group configured for reading
    @type  read : bool
    """
    if parent:
      self.parent = parent
      try:
        self.baseAddress = parent.latchBaseAddr
      except AttributeError:
        if str(parent).split()[0] == 'WBDC2':
          self.baseAddress = 8
        elif str(parent).split()[0] == 'WBDC1':
          self.baseAddress = 80
        else:
          raise ObservatoryError(parent,"is not a known WBDC class")        
    else:
      self.baseAddress = 8
    return self.baseAddress + ((DM-1) << 3) + (int(read) << 2) + (LG-1)
    
  def setLatchAddr(self,read=False):
    """
    select a latch by address

    The latch address is set on EIO0-EIO7, also known as A0-A7 and channels
    8-15.

    @return: boolean
    """
    if read:
      address = self.address | 4
    else:
      address = self.address
    states = [0, address, 0]
    mask = [0, 0xff, 0] # EIO port
    self.logger.debug("  setLatchAddr: writing %s with mask bits %s to select latch %s",
                      states, mask, address)
    try:
      self.LJ.getFeedback(u3.PortStateWrite(State = states, WriteMask = mask))
      return True
    except u3.LabJackException, details:
      self.logger.error("  setLatchAddr: LabJack could not set latch %d\n%s",
                        address, str(details))
      return False

  def read(self):
    """
    read the bit pattern at a latch

    The state of NLOAD is normallly high. When checking status (or reading
    bits), toggle NLOAD low for at least 10 mS then high to store the
    information for reading.

    CS-BUS is the global enable. The normal state is high. Set to this to low
    when programming latches or reading data. Then set high when done.

    @return: byte
    """
    self.logger.debug("  read: Reading latch %d", self.address)
    # Select the latch to be read
    if self.setLatchAddr(read=True):
      port_states = self.LJ.getFeedback(u3.PortStateRead())
      self.logger.debug("  read: port states to check latch address: %s", port_states)
      latchAddr = port_states[0]['EIO']
      #self.logger.debug("  read: LatchGroup address is %d",latchAddr)
      if latchAddr != self.address and latchAddr != (self.address | 4):
        self.logger.debug("  read: Requested latch %d but got %d",
                          self.address, latchAddr)
        return None
      else:
        #self.logger.debug("  read: latch address set to %d", self.address)
        portStates = self.set_signals(
                                 {"SCK":1, "SDI":1,"NLOAD":1, "CS-BUS":1})
        # Store the information to be read from this address
        self.set_signals({"NLOAD":0})
        self.set_signals({"NLOAD":1})
        # Enable serial data transfer
        self.set_signals({"CS-BUS":0})
        MBDATA = 0
        # Process from MS to LS bit
        for bit in range(7,-1,-1):
          try:
            state = self.LJ.getFeedback(
                            u3.BitStateRead(IONumber = WBDCsignal["SDO"]))[0]
            #self.logger.debug("  read: bit %d state is %d for MBDATA = %d",
            #                  bit, state, MBDATA)
          except Exception, details:
            self.logger.error("  read: Data In failed at bit %d\n%s",
                              bit, details)
            return None
          if state:
            MBDATA = Math.Bin.setbit(MBDATA, bit)
          if bit > 0:
            self.set_signals({"SCK":0})
            self.set_signals({"SCK":1})
        self.set_signals({"CS-BUS":1})
        return MBDATA
    else:
      self.logger.error("  read: Setting latch address failed")
      return -1

  def send_bit(self, bit, value):
    """
    """
    self.logger.debug("send_bit: Setting EIO bit %d to %d", bit, value)
    try:
      error = self.LJ.getFeedback(
                                 u3.BitStateWrite(IONumber = WBDCsignal["SDI"],
                                                  State = value))
      # toggle SCK
      self.set_signals({"SCK":0})
      self.set_signals({"SCK":1})
      return True
    except Exception, details:
      print "send_bit: Could not set SDA bit on latch: %s", details
      return False
    #self.logger.debug("send_bit: bit %d state is %d for LATCHDATA =%s",
    #                    EIObit,  bitvalue, Math.decimal_to_binary(LATCHDATA,8))
    
    
  def write(self, LATCHDATA):
    """
    This writes serial data out to a designated latch

    For example, to set the U/L <-> I/Q hybrid switches::
      self.write(lj[1],81,int('01010101',2))

    The operation proceeds as follows::
      # Initialize all signals to high
      # Reset the CS-BUS signal (low)
      # For all data bits from MSB to LSB:
        * Put the bit value on SDI.
        * Toggle SCL
      # Set the CS-BUS signal.

    @type LATCHDATA : int
    @param LATCHDATA : byte to be sent to latch

    @return: bool
    """
    self.logger.debug("write: Writing %s to %s",
                      Math.decimal_to_binary(LATCHDATA,8), self)
    #
    if self.setLatchAddr() == False:
      self.logger.error("write: Failed to set latch address")
      return False
    portStates = self.set_signals({"SCK":1, "SDI":1,"NLOAD":1, "CS-BUS":1})
    latchAddr = portStates['EIO']
    if latchAddr != self.address:
      self.logger.error("write: Requested latch %d but got %d",
                        self.address, latchAddr)
      return False
    self.set_signals({"CS-BUS":0})
    # program latch serially, starting with the MS bit
    for EIObit in range(7,-1,-1):
      # create a bit mask  -- this can be done with Math.Bin.getbit
      bitmask  = 2**EIObit
      # extract the bit from LATCHDATA
      bitvalue = bitmask & LATCHDATA
      self.send_bit(EIObit, bitvalue)
    self.set_signals({"CS-BUS":1})
    return True

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

    @type signal_dict : dictionary
    @param signal_dict : signal names and states

    @return: result of u3.BitStateWrite()
    """
    commands = []
    for signal,state in signal_dict.items():
      commands.append(u3.BitStateWrite(WBDCsignal[signal], state))
    commands.append(u3.PortStateRead())
    self.logger.debug("  set_signals: sending %s", commands)
    try:
      result = self.LJ.getFeedback(commands)
      self.logger.debug("  set_signals: command feedback: %s", result)
      #if float(python_version()[:3]) < 2.6:
      time.sleep(0.01)
    except Exception, details:
      self.logger.error("  set_signals: LJ commands failed:\n%s", details)
    return result[-1]
