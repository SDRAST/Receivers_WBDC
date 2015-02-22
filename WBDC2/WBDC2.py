"""
Module WBDC.WBDC2 provides class WBDC2

Overview
========

For a description of the generic Wide Band Down Converter see/do
MonitorControl.Receivers.WBDC.__doc__.split('\n')

WBDC2 has two signal input pairs, each accepting two orthogonal linear
polarizations. There are two down-converter chains, each handling two
polarizations each, for a total of four complex signals.

Monitor and control is done with two LabJacks. For a detailed description of
the LabJack see/do
MonitorControl.Electronics.Interfaces.LabJack.__doc__.split('\n')

The LabJack with local ID 1 controls and reads switches and reads analog
data (currents, voltages, temperatures) on the motherboard. Details are
described in
/home/kuiper/DSN/technical/Band K/Kband-downconv/Smith-Weinreb/\
WBDC2/DigitalBoard/ControlLogic.ods

LabJacks 2 and 3 control attenuators using TickDACs to provide analog control
voltages.

Motherboard Monitor and Control
===============================

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

Feed Crossover Switch
---------------------

The feed crossover switches are controlled with DM 1 LG 1 using bits L1A0 and
L1A1 (A0, A1 at latchgroup address 8)::
  0 for through
  1 for crossed
The commanded state can be read at the same bits (A0, A1 at LG address 12).
However, the actual state of the cross-over switches are read at L4A0 and
L4A1 (LG address 15).

Polarization Hybrids
--------------------

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

Latch Groups 1,2,3,4 (Address 160,161,162,163)
----------------------------------------------
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
   

Monitoring
==========

Seven latch groups are assigned to digital monitoring, that is, the program
reads the latch states.


Low Address Latch Groups 2 (Address 85) and 3 (Address 86)
----------------------------------------------------------
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
--------------------------------------
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

High Address Latch Groups 1-4 (Addresses 164-168)
-------------------------------------------------
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

Latch Addresses 0 and 2
~~~~~~~~~~~~~~~~~~~~~~~
There are a number of registers used to select analog monitoring points.
An bit pattern sent to latch address 0 selects a current and a voltage
to be connected to AIN0 and AIN1.  A bit pattern sent to latch address
2 selects a thermistor to be connected to AIN2.  AIN3 is not used in this
receiver.

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

LabJack 2 Typical Configuration
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
import copy
import logging
from collections import OrderedDict

import Math
from ... import ComplexSignal, IF, Port, ObservatoryError, show_port_sources
from .. import Receiver
from . import WBDC_base
from .WBDC_core import Attenuator, LatchGroup, WBDC_core
from support import contains

module_logger = logging.getLogger(__name__)

def show_signal(parent, ports):
  inkeys = ports.keys()
  test = ports[inkeys[0]]
  print "\n%s %s signal is %s" % (parent, test, test.signal)
  sigkeys = test.signal.keys()
  for key in sigkeys:
    print "  %s = %s," % (key, test.signal[key]),
  print "\n"

class WBDC2(WBDC_core, Receiver):
  """
  Wideband Downconverter Mod 2

  The down-converter accepts two Beam signals (each consisting of two
  polarization ComplexSignal signals).  It has two down-converters, each of
  which handles one Beam.

  WBDC2 monitor and control logic details are in spreadsheet ControlLogic
  in /usr/local/python/Observatory/Receivers/WBDC/doc.

  The class variable lists 'DC_names' and 'pol_names' will generate input port
  labels D1PA, D1PB, D2PA, D2PB in that order. With the class variable list
  'IF_names', the output port labels will be the above with either I1 or I2
  appended, in that order.
  """
  bands      = ["18", "20", "22", "24", "26"]
  LJIDs = {320053997: 1, 320052373: 2, 320059056: 3}

  def __init__(self, name, inputs = None, output_names=None, active=True):
    """
    Initialize a WBDC2 object.

    @param name : unique identifier
    @type  name : str

    @param inputs : a dict with sources for different inputs
    @type  inputs : dict of str:str

    @param output_names : names of the output channels/ports
    @type  output_names : list of str

    @param active : True is the FrontEnd instance is functional
    @type  active : bool
    """
    self.name = name
    mylogger = logging.getLogger(module_logger.name+".WBDC2")
    mylogger.debug("\ninitializing %s", self)
    show_port_sources(inputs, "WBDC2 inputs before superclass init:",
                        mylogger.level)
    WBDC_core.__init__(self, name, WBDC2.LJIDs,
                       active=active,
                       inputs=inputs,
                       output_names=output_names)               
    show_port_sources(self.inputs, "WBDC2 inputs after superclass init:",
                      mylogger.level)
    show_port_sources(self.outputs, "WBDC2 outputs after superclass init:",
                        mylogger.level)
    self.logger = mylogger

    #self.check_LJ_IO()
    if self.has_labjack(1):
      self.configure_MB_labjack()
    else:
      raise WBDCerror("could not configure motherboard Labjack")
    
    self.data['bandwidth'] = 1e10 # Hz
    # Define the latch groups
    self.lg = {'X':    LatchGroup(parent=self, LG=1),        # crossover (X) switch
               'R1P':  LatchGroup(parent=self, LG=2),        # receiver 1 pol hybrid control
               'R2P':  LatchGroup(parent=self, LG=3),
               'PLL':  LatchGroup(parent=self, LG=4),
               'P1I1': LatchGroup(parent=self, DM=2, LG=1),
               'P1I2': LatchGroup(parent=self, DM=2, LG=2),
               'P2I1': LatchGroup(parent=self, DM=2, LG=3),
               'P2I2': LatchGroup(parent=self, DM=2, LG=4)}
          
    # The transfer switch is created in {\tt WBDC_base}
    self.crossSwitch.get_state()

    # the transfer switch outputs are the RF section inputs
    rfs = self.crossSwitch.outputs.keys()
    rfs.sort()
    self.logger.debug("__init__: transfer switch outputs: %s", rfs)
    self.rf_section = {}
    for rf in rfs:
      index = rfs.index(rf)
      rf_inputs = {}
      outnames = []
      rf_inputs[rf] = self.crossSwitch.outputs[rf]
      self.logger.debug(" __init__: RF %s inputs is now %s", rf, rf_inputs)
      for band in WBDC2.bands:
        outnames.append(rf+band)
      self.rf_section[rf] = self.RFsection(self, rf, inputs = rf_inputs,
                                       output_names=outnames)
      self.logger.debug(" __init__: RF %s outputs is now %s",
                        rf, self.rf_section[rf].outputs)

    # The outputs from the two RFsections for each band go to a pol section
    self.pol_sec = {}
    for band in WBDC2.bands:
      for rx in WBDC_base.RF_names:
        psec_inputs = {}
        psec_name = rx+'-'+band
        for pol in WBDC_base.pol_names:
          psec_inputs[pol] = self.rf_section[rx+pol].outputs[rx+pol+band]
        self.logger.debug(" __init__: PolSection %s inputs is now %s",
                          psec_name, psec_inputs)
        self.pol_sec[psec_name] = self.PolSection(self, psec_name,
                                                inputs = psec_inputs)
        self.pol_sec[psec_name].data['band'] = band
        self.pol_sec[psec_name].data['receiver'] = rx
        self.pol_sec[psec_name]._get_state()
        self.logger.debug(" __init__: pol section %s outputs: %s",
                          self.pol_sec[psec_name].name,
                          self.pol_sec[psec_name].outputs.keys())
    pol_sec_names = self.pol_sec.keys()
    pol_sec_names.sort()
    self.logger.debug(" __init__: pol sections: %s", pol_sec_names)

    self.DC = {}
    for name in pol_sec_names:
      for pol in WBDC_base.out_pols:
        self.logger.debug(" making DC for %s", name+pol)
        self.logger.debug(" creating inputs for %s", name+pol)
        dc_inputs = {name+pol: self.pol_sec[name].outputs[name+pol]}
        self.DC[name+pol] = self.DownConv(self, name+pol,
                                          inputs = dc_inputs)
        rx,band = name.split('-')
        self.DC[name+pol].data['receiver'] = rx
        self.DC[name+pol].data['band'] = band
        self.DC[name+pol].data['pol'] = pol
        self.DC[name+pol]._get_state()
        self.logger.debug(" DC %s created", self.DC[name+pol])
    # report outputs
    self.logger.debug(" %s outputs: %s",
                     self, str(self.outputs))
    self._update_self() # invokes WBDC_base._update_self()
    self.logger.debug(" initialized for %s", self.name)

    # Report outputs
    self.logger.debug(" %s outputs: %s", self, str(self.outputs))
    
  def set_pol_modes(self, circular=False):
    """
    """
    status = {}
    keys = self.pol_sec.keys()
    keys.sort()
    for key in self.pol_sec.keys():
      status[key] = self.pol_sec[key].set_pol_mode(circular=circular)
    return status

  def get_pol_modes(self):
    """
    """
    status = {}
    keys = self.pol_sec.keys()
    keys.sort()
    for key in self.pol_sec.keys():
      status[key] = self.pol_sec[key].get_pol_mode()
    return status

  def set_IF_mode(self, SB_separated=False):
    for key in self.DC.keys():
      self.DC[key].set_IF_mode(SB_separated)
    if SB_separated:
      self.data['bandwidth'] = 1e9
    else:
      self.data['bandwidth'] = 2e9
    return self.get_IF_mode()

  def get_IF_mode(self):
    modes = {}
    keys = self.DC.keys()
    keys.sort()
    for key in self.DC.keys():
      modes[key] = self.DC[key].get_IF_mode()
    return modes

  def check_IO_config(self):
    """
    Check the configuration of this LabJack according ot its local ID.

    The local ID should reflect its function in WBDC2:
      1 - motherboard control
      2 - receiver 1 attenuators
      3 - receiver 2 attenuators
    """
    # Is there a motherboard controller?
    if self.has_labjack(1):
      # A MB controller has F bits 0-3 set for analog input
      if self.LJ[1].configIO()['FIOAnalog'] != 15:
        self.logger.info(
                       "check_IO_config: Configuring LabJack 1 for MB control")
        self.configure_MB_labjack()
    else:
      raise ObservatoryError("","LabJack 1 is not connected")
    if self.has_labjack(2):
      # A LJ with a TickDAC mounted on an FIO section has that section
      # configured for digital output.
      if self.LJ[2].configU3()['EIOState']!= 255:
        self.logger.info(
               "check_IO_config: Configuring LabJack 2 for attenuator control")
        self.configure_atten_labjack(2)
    else:
      raise ObservatoryError("","LabJack 2 is not connected")
    if self.has_labjack(3):
      if self.LJ[3].configU3()['EIOState']!= 255:
        self.logger.info(
               "check_IO_config: Configuring LabJack 3 for attenuator control")
        self.configure_atten_labjack(3)
    else:
      raise ObservatoryError("","LabJack 3 is not connected")
    
  class TransferSwitch(WBDC_core.TransferSwitch):
    """
    Beam to down-converter transfer switch

    There is one Switch object for each front-end polarization P1 and P2.
    

    At some point this might become a general transfer switch class
    """
    def __init__(self, parent, name, inputs=None, output_names=None):
      mylogger = logging.getLogger(parent.logger.name+".TransferSwitch")
      self.name = name
      WBDC_core.TransferSwitch.__init__(self, parent, name, inputs=inputs,
                                        output_names=output_names)
      mylogger.debug(" initializing %s", self)
      mylogger.debug(" %s inputs: %s", self, str(self.inputs))
      self.parent = parent
      self.logger = mylogger
        
    def get_state(self):
      """
      Get the state of the beam cross-over switches
      """
      keys = self.data.keys()
      self.logger.debug("WBDC2.TransferSwitch.get_state: checking switches %s", keys)
      return super(WBDC2.TransferSwitch,self).get_state()

    class Xswitch(WBDC_core.TransferSwitch.Xswitch):
      """
      """
      def __init__(self, parent, name, inputs=None, output_names=None,
                   active=True):
        self.name = name
        WBDC_core.TransferSwitch.Xswitch.__init__(self, parent, name,
                                                  inputs=inputs,
                                                  output_names=output_names,
                                                  active=active)

      def _get_state(self):
        """
        Get the state from the hardware switch.

        The switch is sensed by bit 0 or 1 of the latch group at address 87
        Labjack 1. Low (value = 0) is for through and high is for crossed.

        Since latch group 1 also controls the IQ hybrids we need to read their
        states and make sure their bits remain the same.

        WBDC2 is different from WBDC1 in the use of the latchgroup bits.

        """
        self.logger.debug("_get_state:  for %s", self)
        rx = self.parent.parent # WBDC_core instance which owns the latch group
        try:
          status = rx.lg['PLL'].read()
          self.logger.debug("_get_state: Latch Group %s data = %s", rx.lg['PLL'],
                            Math.decimal_to_binary(status,8))
          test_bit = WBDC_base.pol_names.index(self.name)+1
          self.state = bool(status & test_bit)
          self.logger.debug("_get_state: %s switch state = %d", self, self.state)
        except AttributeError, details:
          self.logger.error("WBDC_core.TransferSwitch.Xswitch._get_state: %s", details)
        return self.state

      def _set_state(self, crossover=False):
        """
        Set the RF transfer (crossover) switch

        The switch is controlled by bits 0 and 1 of latch group 1 (address 80)
        of Labjack 1. Low (value = 0) is for crossed and high is for through.
        """
        self.logger.debug("WBDC2.TransferSwitch.Xswitch._set_state:  for %s", self)
        rx = self.parent.parent # WBDC_core instance which owns the latch group
        # get the current bit states
        try:
          status = rx.lg['X'].read()
          self.logger.debug("_set_state: Latch Group %s data = %s", rx.lg['X'],
                            Math.decimal_to_binary(status,8))
        except AttributeError, details:
          self.logger.error("_set_state: status read failed: %s", details)
          return False
        ctrl_bit = WBDC_base.pol_names.index(self.name)
        if crossover:
          value = Math.Bin.setbit(status, ctrl_bit)
        else:
          value = Math.Bin.clrbit(status, ctrl_bit)
        try:
          self.logger.debug("_set_state: writing %s",
                            Math.decimal_to_binary(value,8))
          status = rx.lg['X'].write(value)
          if status:
            self.logger.debug("_set_state: write succeeded")
          else:
            self.logger.error("_set_state: write failed")
        except AttributeError, details:
          self.logger.error("_set_state: write failed: %s", details)
          return False
        self.state = self._get_state()
        self.logger.debug("_set_state: Xswitch state = %d", self.state)
        return self.state

  class RFsection(WBDC_core.RFsection):
    """
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      self.parent = parent
      self.name = name
      mylogger = logging.getLogger(module_logger.name+".RFsection")
      mylogger.debug(" initializing WBDC2 %s", self)
      show_port_sources(inputs,
                        "WBDC2.RFsection inputs before superclass init:",
                        mylogger.level)
      WBDC_core.RFsection.__init__(self, parent, name, inputs=inputs,
                                  output_names=output_names, active=True)
      show_port_sources(self.inputs,
                        "WBDC_base.RFsection inputs after superclass init:",
                        mylogger.level)
      show_port_sources(self.outputs,
                        "WBDC_base.RFsection outputs after superclass init:",
                        mylogger.level)
      self.logger = mylogger
      self._redefine_outputs()
      self._update_self()

    def _redefine_outputs(self):
      """
      """
      for key in self.outputs.keys():
        self.logger.debug(
                 "WBDC_core.RFsection._redefine_outputs: for %s, source is %s",
                 key, self.outputs[key].source)
        self.logger.debug(
                 "WBDC_core.RFsection._redefine_outputs: source signal is %s",
                 self.outputs[key].source.signal)
        # The RF section does not change the signal type but makes sub-bands
        self.outputs[key] = Port(self, key,
                                 source=self.outputs[key].source,
                         signal=ComplexSignal(self.outputs[key].source.signal))
        
    def _update_self(self):
      """
      Update the signals at the outputs
      """
      self.logger.debug("_update_self: updating %s", self.name)
      # connect the ports
      self._propagate()
      # update the signals
      outnames = self.outputs.keys()
      outnames.sort()
      for key in self.inputs.keys():
        if hasattr(self.inputs[key].signal,'copy'):
          self.logger.debug("_update_self: processing input port %s", key)
          self.inputs[key].signal.copy(self.inputs[key].source.signal)
          for outkey in outnames:
            self.outputs[outkey].signal = ComplexSignal(self.inputs[key].signal)
            self.outputs[outkey].signal.name = outkey
            self.logger.debug(" _update_self: output port %s signal is %s",
                              outkey, self.outputs[outkey].signal)
            self.outputs[outkey].signal['bandwidth'] = 2 # GHz
            self.outputs[outkey].signal['frequency'] = float(outkey[-2:])
         
  class PolSection(WBDC_core.PolSection):
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
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      """
      """
      mylogger = logging.getLogger(parent.logger.name+".PolSection")
      self.name = name
      mylogger.debug(" initializing %s", self)
      WBDC_core.PolSection.__init__(self, parent, name, inputs=inputs,
                                  output_names=output_names,
                                  active=active)
      self.logger = mylogger
      self.logger.debug(" __init__: output names: %s",
                        output_names)
      self.logger.debug(" initializing WBDC2 %s", self)
      self.logger.debug(" %s inputs: %s", self, str(self.inputs))
      keys = self.outputs.keys()
      keys.sort()
      inkeys = self.inputs.keys()
      inkeys.sort()
      for key in keys:
        indx = keys.index(key)
        inname = inkeys[indx]
        # A pol section does not change the signal type
        self.outputs[key] = Port(self, key,
                                 source=self.inputs[inname],
                         signal=ComplexSignal(self.inputs[inname].signal))
      self.logger.debug(" %s outputs: %s", self, str(self.outputs))

    def _get_state(self):
      """
      Returns the state of the polarization conversion section.

      X,Y are converted to L,R if the state is 1.

      The pol section needs to know what band it belongs to to know what
      latches to use.
      """
      LGID = self.data['receiver']+'P'
      LG = int(self.data['receiver'][-1])+1
      latchbit = (int(self.data['band'])-18)/2
      LGdata = self.parent.lg[LGID].read()
      self.state = Math.Bin.getbit(LGdata,latchbit)
      return self.state

    def _set_state(self,state):
      """
      Sets the state of the polarization conversion section.

      If set, X,Y are converted to L,R.

      The pol section needs to know what band it belongs to to know what
      latches to use.
      """
      LGID = self.data['receiver']+'P'
      LG = int(self.data['receiver'][-1])+1
      latchbit = (int(self.data['band'])-18)/2
      LGdata = self.parent.lg[LGID].read()
      self.parent.lg[LGID].write(Math.Bin.setbit(LGdata,latchbit))
      self._get_state()
      self._update_self()
      return self.state

    class IFattenuator(Attenuator):
      """
      """
      def __init__(self, LabJack, IOport):
        Attenuator.__init__(self, LabJack, IOport)

    def get_atten(self, pol):
      """
      Returns attenuation for `pol' inputs of pol section
      """
      
      
  class DownConv(WBDC_core.DownConv):
    """
    Converts RF to IF

    A hybrid optional converts the I and Q IFs to LSB and USB.
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      """
      """
      mylogger = logging.getLogger(module_logger.name+".DownConv")
      self.name = name
      #show_signal(self, inputs)
      WBDC_core.DownConv.__init__(self, parent, name, inputs=inputs,
                                 output_names=output_names,
                                 active=active)
      self.parent = parent
      self.logger = mylogger
      super(WBDC_core.DownConv, self).set_IF_mode() # default is bypass
      keys = self.outputs.keys()
      keys.sort()
      self.logger.debug(" outputs: %s", keys)
      for key in keys:
        IFname = key[-2:]
        index = WBDC_base.IF_names.index(IFname)
        IFmode = self.get_IF_mode()[index] # self.IF_mode[index]
        self.logger.debug(" %s IF mode is %s", key, IFmode)
        self.outputs[key] = Port(self, key,
                       source=self.outputs[key].source,
                    signal=IF(self.outputs[key].source.signal, IF_type=IFmode))
        self.parent.outputs[key] = self.outputs[key]

    def _get_latch_info(self):
      """
      """
      self.logger.debug("_get_latch_info: called for pol %s, band %s, rx %s",
                        self.data['pol'],
                        self.data['band'],
                        self.data['receiver'])
      rxno = int(self.data['receiver'][-1])-1
      if int(self.data['band']) < 21:
        LGID = self.data['pol']+'I1'
        latchbit = int(self.data['band']) - 18 + rxno
      else:
        LGID = self.data['pol']+'I2'
        latchbit = int(self.data['band']) - 22 + rxno
      self.logger.debug("_get_latch_info: latch bit %d on group %s selected",
                        latchbit, LGID)
      return LGID, latchbit
      
    def _get_state(self):
      """
      """
      LGID, latchbit = self._get_latch_info()
      try:
        latchdata = self.parent.lg[LGID].read()
      except Exception, details:
        self.logger.error("_get_state: read failed: %s", str(details))
      self.state = Math.Bin.getbit(latchdata, latchbit)
      return self.state
      
    def _set_state(self,state):
      """
      """
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
      self._get_state()
      self._update_self()
      return self.state
      