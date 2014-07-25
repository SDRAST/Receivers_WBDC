# -*- coding: utf-8 -*-
"""
Monitor and Control of Wideband Downconverter with LabJack

For more details, diagrams and test results please visit
http://dsnra.jpl.nasa.gov/eng-wiki/index.php?title=Wideband_K-band_Downconverter

Wideband Downconverter
======================

Overview
--------
The prototype WBDC has two inputs, each producing two orthogonal linear
polarizations.  There are two down-converter chains, each handling two
polarizations, for a total of four signals.

Input Switching
---------------
The first stage of the WBDC allows the down-converter pairs to be switched
between the two feeds.

Polarization Conversion
-----------------------
The linearly polarized signals from each feed can be switched into a
quadrature hybrid to be converted to cicular polarizations.

Band Selection
--------------
There are two programmable local oscillators and a switch selects between
to define the band to be down-converted.

Sideband Separation
-------------------
The down-conversion produces complex outputs (i.e. a pair of signals I and
Q).  There are switches which can direct each I/Q pair into a quadrature
hybrid to convert them to an upper and lower sideband pair.

Module Functions
================
These are the functions in this module that handle WBDC I/O::
  set_signals(LJ,signal_dict)
  setLatchAddr(LJ,LATCHNUM)
  readLatch(LJ,LATCHNUM)
  get_latch_states(LJ,latchlist)
  programLatch(LJ,LATCHNUM,LATCHDATA)
  readAnalog(LJ,mon_points)
  get_monitor_data(lj)

These function get or set the WBDC configuration::
  feeds_swapped(lj)
  pol_is_circular(lj)
  selected_band(lj)
  PLOs_locked(lj)
  reset_to_default(LJ,factory=False)
  init_WBDC_U3s()
  report_WBDC_state()
"""
import sys
import re
import u3
import time
import struct
import scipy
import numpy as NP
from scipy.optimize import bisect
from u3 import U3

import Math
from Electronics.Interfaces.LabJack import LJTickDAC
import Electronics.Interfaces.LabJack as LJif

diag_set_signals = False
diag_set_latch_addr = False
diag_read_latch = False
diag_write_latch = False
diag_read_analog = False
diag_monitor_data = False
diag_pol = False

# These map the signal names into the LabJack digital IO lines.
# Note that 
WBDCsignal = {
  'IMON':0, 'VMON':1, 'TEMP':2, 'LNA':3, 'SDO':7,
  'A0':8, 'A1':9, 'A2':10, 'A3':11, 'A4':12, 'A5':13, 'A6':14, 'A7':15,
  'SCK':16, 'SDI':17, 'NLOAD':18, 'CS-BUS':19}

LJif.U3name['320038183'] = "WBDC Atten. Control"
LJif.U3name['320038583'] = "WBDC Switch/Sensors"

# Something which will drive you crazy when you read the VB code is that
# the four analog channels are named ANALOG0, ANALOG1, ANALOG3 and ANALOG4.
mon_points = { 1: [[0, int('00000000',2)],[2, int('00000000',2)]],
               2: [[0, int('00001001',2)],[2, int('00010000',2)]],
               3: [[0, int('00010100',2)],[2, int('00100000',2)]],
               4: [[0, int('01011011',2)],[2, int('00110000',2)]],
               5: [[0, int('01100010',2)],[2, int('01000000',2)]],
               6: [[0, int('10100000',2)],[2, int('01010000',2)]],
               7: [[0, int('10101000',2)],[2, int('01100000',2)]],
               8: [[0, int('00000000',2)],[2, int('01110000',2)]]}

                                                          # WBDC label
mon_ID = { 1: [" +6V DC I",  " +6V DC V", ""],
           2: [" +6V AC I",  " +6V AC V", ""],
           3: ["-16V DC I",  "-16V AC V", "Air"],         # unlabelled
           4: ["+16V I RF1", "+12V V",    ""],
           5: ["+16V I RF2", "+16V V",    "RF 1 Plate"],  # Temp 4
           6: ["+16V I IF1", "",          "RF 2 Plate"],  # Temp 3
           7: ["+16V I IF2", "",          "Box Wall"],    # Temp 2
           8: ["",           "",          "LDROs"]}       # Temp 1

IOFFSET     =  0.004   # zero current reading
VSCALElo    =  4.0211  # scale factor for 5V measurements
VSCALEhi    = 10.5542  # scale factor for 12 and 16 V measurements
THERMOFFSET =  0.16    # analog reading for 0 deg C
THERMSCALE  = 20.0     # temperature reading scale factor
  
def set_signals(LJ,signal_dict):
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
    commands.append(u3.BitStateWrite(WBDCsignal[signal],state))
  commands.append(u3.PortStateRead())
  if diag_set_signals:
    print "set_signals sending",commands
  try:
    result = LJ.getFeedback(commands)
    if diag_set_signals:
      print "set_signals command feedback:",result
    time.sleep(0.01)
  except Exception, details:
    print "LJ commands failed"
    print details
  return result[-1]

def setLatchAddr(LJ,LATCHNUM):
  """
  select a latch by address

  @type LJ : u3.U3 class instance
  @param LJ : LabJack which controls the latches

  @type LATCHNUM : int
  @param LATCHNUM : number of latch to be addressed

  @return: boolean
  """
  states = [0,LATCHNUM,0]
  mask = [0,0xff,0] # EIO port
  if diag_set_latch_addr:
    print "setLatchAddr: writing",states,"to bits",mask,"to select latch",LATCHNUM
  try:
    LJ.getFeedback(u3.PortStateWrite(State = states, WriteMask = mask))
    return True
  except u3.LabJackException, details:
    print "setLatchAddr: LabJack could not set latch",LATCHNUM
    print details
    return False

def readLatch(LJ,LATCHNUM):
  """
  read the bit pattern at a latch

  @type LJ : u3.U3 class instance
  @param LJ : LabJack controlling the latch

  @type LATCHNUM : int
  @param LATCHNUM : latch address

  @return: byte
  """
  if diag_read_latch:
    print "readLatch: Reading latch",LATCHNUM
  # Select the latch to be read
  if setLatchAddr(LJ,LATCHNUM):
    port_states = LJ.getFeedback(u3.PortStateRead())
    if diag_read_latch:
      print "port states:", port_states
    latchAddr = port_states[0]['EIO']
    if diag_read_latch:
      print "readLatch: Latch address is",latchAddr
    if latchAddr != LATCHNUM:
      print "readLatch: Requested latch",LATCHNUM,"but got",latchAddr
      return None
    else:
      if diag_read_latch:
        print "latch address set to",LATCHNUM
      portStates = set_signals(LJ,{"SCK":1, "SDI":1,"NLOAD":1, "CS-BUS":1})
      # Store the information to be read from this address
      set_signals(LJ,{"NLOAD":0})
      set_signals(LJ,{"NLOAD":1})
      # Enable serial data transfer
      set_signals(LJ,{"CS-BUS":0})
      MBDATA = 0
      # Process from MS to LS bit
      for bit in range(7,-1,-1):
        try:
          state = LJ.getFeedback(u3.BitStateRead(IONumber = WBDCsignal["SDO"]))[0]
          if diag_read_latch:
            print "readLatch: bit",bit,"state is",state,"for MBDATA =",MBDATA
        except Exception, details:
          print "readLatch: Data In failed at bit",bit
          print details
          return None
        if state:
          MBDATA = Math.Bin.setbit(MBDATA,bit)
        if bit > 0:
          set_signals(LJ,{"SCK":0})
          set_signals(LJ,{"SCK":1})
      set_signals(LJ,{"CS-BUS":1})
      return MBDATA
  else:
    print ">>> Setting latch address failed"
    return -1

def get_latch_states(LJ, latchlist):
  """
  Returns the state of the designated latches.

  The latch LED positions are:
  UL = 86   UR = 87
  LL = 84   LR = 85
  
  Example output for lj[1] with::
    feeds not crossed over
    linear polarization
    I/Q IFs
    In [3]: get_latch_states(lj[1],[84,85,86,87])
    Out[3]: {84: '00001101', 85: '01010101', 86: '01011010', 87: '00011111'}

  @type LJ : u3.U3 class instance
  @param LJ : LabJack controlling the latches

  @type latchlist : list of int
  @param latchlist : latch numbers to be checked

  @return: dictionary
  """
  states = {}
  for latch in latchlist:
    states[latch] = Math.decimal_to_binary(readLatch(LJ,latch),8)
  return states
  
def programLatch(LJ,LATCHNUM,LATCHDATA):
  """
  This writes serial data out to a designated latch

  To set the U/L <-> I/Q hybrid switches::
    programLatch(lj[1],81,int('01010101',2))
  

  @type LJ : u3.U3 class instance
  @param LJ : LabJack controlling the latch

  @type LATCHNUM : int
  @param LATCHNUM : latch address

  @type LATCHDATA : int
  @param LATCHDATA : byte to be sent to latch

  @return: bool
  """
  if diag_write_latch:
    print "programLatch: Writing",Math.decimal_to_binary(LATCHDATA,8),"to LATCH",LATCHNUM
  if setLatchAddr(LJ,LATCHNUM) == False:
    print "programLatch: Failed to set latch address"
    return False
  portStates = set_signals(LJ,{"SCK":1, "SDI":1,"NLOAD":1, "CS-BUS":1})
  latchAddr = portStates['EIO']
  if diag_write_latch:
    print "programLatch: Latch address is",Math.decimal_to_binary(latchAddr,8)
  if latchAddr != LATCHNUM:
    print "programLatch:Requested latch",LATCHNUM,"but got",latchAddr
    return False
  set_signals(LJ,{"CS-BUS":0})
  # program latch, starting with the MS bit
  for EIObit in range(7,-1,-1):
    # create a bit mask
    bitmask  = 2**EIObit
    # extract the bit from LATCHDATA
    bitvalue = bitmask & LATCHDATA
    if diag_write_latch:
      print "programLatch: Setting EIO bit",EIObit,"(",
      print Math.decimal_to_binary(bitmask,8),") to",
      print bitvalue
    try:
      error = LJ.getFeedback(u3.BitStateWrite(IONumber = WBDCsignal["SDI"],
                                              State = bitvalue))
    except Exception, details:
      print "programLatch: Could not set SDA bit on latch", LATCHNUM
      print details
      return False
    if diag_write_latch:
      print "programLatch: bit", EIObit, "state is", bitvalue, \
            "for LATCHDATA =", Math.decimal_to_binary(LATCHDATA,8)
    # toggle SCK
    set_signals(LJ,{"SCK":0})
    set_signals(LJ,{"SCK":1})
  set_signals(LJ,{"CS-BUS":1})
  return True

def readAnalog(LJ,mon_points):
  """
  Read analog monitor data
  
  The array 'mon_points' holds the latch address and latch data select
  pair for each reading to be taken.  Then three analog ports are
  read.

  @type LJ : u3.U3 class instance
  @param LJ : LabJack controlling the latches

  @type mon_points : list of lists
  @param mon_points : list of latch number, latch data pairs

  @return: list of three analog values
  """
  readings = []
  num_analog_ports = 3
  if diag_read_analog:
    print "Reading monitor points",mon_points
  for [latchnum,latchdata] in mon_points:
    if (latchnum != None) and (latchdata != None):
      programLatch(LJ, latchnum, latchdata)
      if diag_read_analog:
        print "Latch",latchnum,"programmed with",latchdata
  for i in range(num_analog_ports):
    try:
      reading = LJ.getAIN(i)
    except u3.LowlevelErrorException, details :
      print "\nReading analog port",i,"failed"
      print details
    else:
      readings.append(reading)
  return readings


def get_monitor_data(lj):
  """
  Gets the analog currents, voltages and temperatures

  @type lj : dictionary
  @param lj : u3.U3 class instances indexed by local ID

  @return: dictionary
  """
  LJ = lj[1]
  mon_data = {}
  for i in range(1,9):
    if diag_monitor_data:
      print "Mon group",i,":",
    readings = readAnalog(LJ,mon_points[i])
    if diag_monitor_data:
      print mon_ID[i]
      print readings
    for j in range(3):
      if j == 0 and mon_ID[i][j]:
        # calibrate current
        mon_data[mon_ID[i][j]] = readings[j] - IOFFSET
      elif j == 1 and mon_ID[i][j]:
        #calibrate voltage
        if i < 3:
          # 6 V
          mon_data[mon_ID[i][j]] = readings[j] * VSCALElo
        elif i < 6:
          # 12or 16 V
          mon_data[mon_ID[i][j]] = readings[j] * VSCALEhi
      elif j == 2 and mon_ID[i][j]:
        # temperature
        mon_data[mon_ID[i][j]] = (readings[j] - THERMOFFSET) * THERMSCALE
  return mon_data
  
def feeds_swapped(lj):
  """
  Report feed switch cross-over state

  @type lj : dictionary
  @param lj : u3.U3 class instances indexed by local ID

  @return: bool
  """
  latchnum = 87
  latchValue = readLatch(lj[1],latchnum)
  if latchValue == None:
    return None
  else:
    bits = latchValue & 3
    if bits == 0:
      return False
    elif bits == 3:
      return True
    else:
      return None

def pol_is_circular(lj):
  """
  Report whether feed polarization is circular.

  Latch 3 (address 86) monitors the polarizer switches.  Bit pattern 01
  indicates linear polarization. Bit pattern 10 indicates circular
  polarization. Bits 1 and 2 (mask 00000110 = 0x6) monitor polarizer 1.
  Bits 3 and 4 (mask 00011000 = 0x18) monitor polarizer 2.
  
  @type lj : dictionary
  @param lj : u3.U3 class instances indexed by local ID

  @return: list of bool
  """
  latchnum = 86
  bits = readLatch(lj[1],latchnum)
  if bits == None:
    return [None,None]
  else:
    if diag_pol:
      print "pol_is_circular: latch bits:",Math.decimal_to_binary(bits,8)
    pol1bits = bits & 15
    if diag_pol:
      print "pol_is_circular: pol1 bits:",Math.decimal_to_binary(pol1bits,8)
    if  pol1bits == int('1010',2):
      circular = [False]
    elif pol1bits == int('0101',2):
      circular = [True]
    else:
      circular = [None]
    pol2bits = (bits & 240) >> 4
    if diag_pol:
      print "pol_is_circular: pol2 bits:",Math.decimal_to_binary(pol2bits,8)
    if pol2bits == int('0101',2):
      circular.append(False)
    elif pol2bits == int('1010',2):
      circular.append(True)
    else:
      circular.append(None)
    return circular

def selected_band(lj):
  """
  Report selected band center frequency in GHz
  
  @type lj : dictionary
  @param lj : u3.U3 class instances indexed by local ID

  @return: int
  """
  latchnum = 87
  bits = readLatch(lj[1],latchnum)
  if bits >= 0:
    if Math.Bin.getbit(bits,2):
      return 22
    else:
      return 24
  else:
    print "selected band: readLatch returned",bits
    return 0

def PLOs_locked(lj):
  """
  Report lock state of PLOs

  @type lj : dictionary
  @param lj : u3.U3 class instances indexed by local ID

  @return: list of bool
  """
  latchnum = 87
  bits = readLatch(lj[1],latchnum)
  if bits == None:
    return None
  else:
    if Math.Bin.getbit(bits,2):
      locked = [True]
    else:
      locked = [False]
    if Math.Bin.getbit(bits,3):
      locked.append(True)
    else:
      locked.append(False)
    return locked

def reset_to_default(LJ,factory=False):
  """
  Return LabJack to power-up configuration
  
  Notes
  =====
  u3 function LJ_ioPIN_CONFIGURATION_RESET is only supported for Windows.

  @type LJ : u3.U3 class instance
  @param LJ : LabJack

  @return: bool (True on success)
  """
  # Need LJ ID for any reporting
  localID = LJ.localID
  if sys.platform[:5] == "linux":
    try:
      LJ.setDefaults(SetToFactoryDefaults=factory)
      return True
    except Exception, details:
      print "reset_to_default: Could not set LJ",localID,"defaults"
      return False
  else:
    # Try Windows
    try:
      u3.ePut(LJ, u3.LJ_ioPIN_CONFIGURATION_RESET, 0, 0, 0)
      return True
    except Exception, details:
      print "reset_to_default: Could not reset LJ",localID
      print details
      return False

def init_WBDC_U3s(lj):
  """
  Initialize LabJack U3s for the WBDC (Wideband Downconverter)

  The digital bit directions are::
    0 - in
    1 - out

  @return: dictionary of u3.U3 class instances
  """
  ljs_configured = []
  for LJ in lj.keys():
    if reset_to_default(lj[LJ],factory=False):
      if LJ == 1:
        FIOanalog = int('00001111',2)
        lj[LJ].configIO(FIOAnalog=FIOanalog,EIOAnalog=0)
        CIOBitDir = int('1111',2)
        EIOBitDir = int('11111111',2)
        FIOBitDir = int('00000000',2)
        direction = [FIOBitDir, EIOBitDir, CIOBitDir]
        mask = [0xff,0xff,0xff]
      elif LJ == 2:
        lj[LJ].configIO(EIOAnalog=0, FIOAnalog=0)
        CIOBitDir = int('0000',2)
        EIOBitDir = int('00000000',2)
        FIOBitDir = int('00000000',2)
        direction = [FIOBitDir, EIOBitDir, CIOBitDir]
        mask = [0xff,0xff,0xff]
      elif LJ == 3:
        # front end LabJack:
        lj[LJ].configIO(FIOAnalog=0)
        lj[LJ].configAnalog(u3.EIO2, u3.EIO3,
                            u3.EIO4, u3.EIO5,
                            u3.EIO6)
        lj[LJ].configDigital(u3.EIO0, u3.EIO1,u3.EIO7)
        CIOBitDir = int('0000',2)
        EIOBitDir = int('10000000',2)
        FIOBitDir = int('00111111',2)
        direction = [FIOBitDir, EIOBitDir, CIOBitDir]
        mask = [0xff,0xff,0xff]
      print "LabJack",LJ,"direction=",direction,"write mask=",mask
      try:
        lj[LJ].getFeedback(u3.PortDirWrite(Direction=direction,
                                           WriteMask=mask))
      except Exception, details:
        print "Could not set bit direction on U3",LJ
        print details
      else:
        ljs_configured.append(LJ)
    else:
      print "Could not set Labjack",LJ,"to default state"
  return ljs_configured

def set_crossover(lj,crossed):
  """
  Set the feed/receiver cross-over switches

  @type crossed : boolean
  @param crossed : True for feed 1 to go to receiver 2 and vice versa

  @return: True on success
  """
  # first find the state of the polarizers and PLO selector
  rx1_pol_is_circ, rx2_pol_is_circ = pol_is_circular(lj)
  if rx1_pol_is_circ == None:
    rx1_pol_is_circ = False
    print "Rx1 circular is set to",rx1_pol_is_circ
  if rx2_pol_is_circ == None:
    rx2_pol_is_circ = False
    print "Rx2 circular is set to",rx2_pol_is_circ
  print "Rx1 circ pol:",rx1_pol_is_circ,"Rx2 circ pol:", rx2_pol_is_circ
  # the other thing controlled by latch 1 is the PLO select
  # now form and send the latch data
  latchdata = int(crossed)
  if rx1_pol_is_circ:
    latchdata += int('00000010',2)
  else:
    latchdata += int('00000100',2)
  if rx2_pol_is_circ:
    latchdata += int('00010000',2)
  else:
    latchdata += int('00001000',2)
  band = selected_band(lj)
  latchdata += int(band > 23) * 32
  if programLatch(lj[1], 80, latchdata):
    if diag_write_latch:
      print "set_crossover: sending",Math.decimal_to_binary(latchdata,8),"to latch address 80"
    return True
  else:
    print "Failed to program latch 80"
    return False

def set_polarizers(lj, circular=False):
  """
  Sets both polarization convertors to the same state.

  The native polarizations of the feeds are linear.  By means of
  quadrature hybrids they can be converted to circular polarization.

  @type circular : bool
  @param circular : True to convert linear polarixation to circular

  @return: True on success
  """
  # find the state of the front end switch
  crossed_over = feeds_swapped(lj)
  if crossed_over == None:
    set_crossover(lj,False)
    crossed_over = False
    print "Feed swap is set to",crossed_over
  else:
    print "Feed swap is",crossed_over
  # find the state of the PLO select
  # now form and send the latch data
  latchdata = int(crossed_over)
  if circular:
    latchdata += int('00010010',2)
  else:
    latchdata += int('00001100',2)
  band = selected_band(lj)
  print "Band is",band
  latchdata += int(band > 23) * 32
  if programLatch(lj[1], 80, latchdata):
    if diag_write_latch:
      print "Sending",Math.decimal_to_binary(latchdata,8),"to latch address 80"
    return True
  else:
    print "Failed to program latch 80"
    return False
  
def set_band(lj, freq):
  """
  Select the frequency band.

  This switches between PLOs for either 21-23 GHz or 23-25 GHz

  @type freq : int
  @param freq : freq (GHz) at band center

  @return: True on success
  """
  # first find the state of the polarizers and PLO selector
  rx1_pol_is_circ, rx2_pol_is_circ = pol_is_circular(lj)
  # Now form the latchdata
  latchdata = int(feeds_swapped(lj))
  if rx1_pol_is_circ:
    latchdata += int('00000010',2)
  else:
    latchdata += int('00000100',2)
  if rx2_pol_is_circ:
    latchdata += int('00010000',2)
  else:
    latchdata += int('00001000',2)
  latchdata += int(freq > 23) * 32
  if programLatch(lj[1], 80, latchdata):
    if diag_write_latch:
      print "Sending",Math.decimal_to_binary(latchdata,8),"to latch address 80"
    return True
  else:
    print "Failed to program latch 80"
    return False

def channels_are_UL(lj):
  """
  Reports whether the receiver channels do I/Q -> U/L conversion.

  The complex mixers deliver two baseband signals in quadrature,
  i.e., one shifted 90 deg in phase.  Quadrature hybrids can
  be used to provide two streams of data, one for the 1 GHz band
  above the LO and the other below the LO.

  Boolean data are keyed by receiver and channel.

  @return: dictionary
  """
  receivers = [0,1]
  channels = [0,1]
  UL = {}
  latchdata = readLatch(lj[1],85)
  print Math.decimal_to_binary(latchdata,8)
  for rx in receivers:
    UL[rx] = {}
    for ch in channels:
      shift = 2*(ch + 2*rx)
      bits = ((0x3 << shift) & latchdata) >> shift
      print "Receiver",rx,"channel",ch,"bits:",bits
      if (bits/2-1):
        UL[rx][ch] = True
      else:
        UL[rx][ch] = False
  return UL

def set_UL_switch(lj,receiver,channel,convert=False):
  """
  Set one receiver channel to convert I/Q to U/L or not.

  @type receiver : int
  @param receiver : receiver number 0 or 1

  @type channel : int
  @param channel : receiver number 0 or 1

  @type convert : boolean
  @param convert : True to convert I/Q to U/L.

  @return: True on success
  """
  # first get the state of the latches
  latchdata = readLatch(lj[1],85)
  # Now calculate the bit pattern to be set
  shift = 2*(channel + 2*receiver)
  mask = 3 << shift
  value = latchdata & mask
  latchdata -= value
  if convert:
    bitpair = int('01',2)
  else:
    bitpair = int('10',2)
  new_latchdata = latchdata | (bitpair << shift)
  if programLatch(lj[1], 81, new_latchdata):
    return True
  else:
    print "Failed to program latch 81"
    return False

def set_UL_switches(lj,states):
  """
  Set all I/Q to U/L convertors

  @type states : list of boolean
  @param states : conversion option list [rx 0 ch 0, rx 0 ch 1, rx 1...]

  @return: True on success
  """
  receivers = [0,1]
  channels = [0,1]
  latchdata = 0
  for rx in receivers:
    for ch in channels:
      index = 2*rx + ch
      shift = 2*index
      if states[index]:
        bits = int('01',2)
      else:
        bits = int('10',2)
      latchdata += bits << shift
      print rx,ch,Math.decimal_to_binary(latchdata,8)
  if programLatch(lj[1], 81, latchdata):
    return True
  else:
    print "Failed to program latch 81"
    return False
