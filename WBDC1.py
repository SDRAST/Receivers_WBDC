"""
Module WBDC.WBDC1 provides class WBDC1

For a description of the generic Wide Band Down Converter see/do
MonitorControl.Receivers.WBDC.__doc__.split('\n')

WBDC1 has two input pairs, each accepting two orthogonal linear polarizations.
There are two down-converter chains, each handling two polarizations each, for
a total of four complex signals.

WBDC1 Band Selection
====================
There are two programmable local oscillators and a switch selects between
to define the band to be down-converted.  This is a WBDC1-unique feature.

Monitor and control is done with two LabJacks. For a detailed description of
the LabJack see/do
MonitorControl.Electronics.Interfaces.LabJack.__doc__.split('\n')

The LabJack with local ID 1 controls and reads switches, and reads analog
data (currents, voltages, temperatures). Details are described in
/home/kuiper/DSN/technical/Band K/Kband-downconv/Smith-Weinreb/\
WBDC1/DigitalBoard/ControlLogic.ods

LabJack 2 controls attenuators using TickDACs to provide analog control
voltages.


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

from ... import IF, Port
from .. import Receiver
from . import WBDC_base
from .WBDC_core import WBDC_core
from support import contains

class WBDC1(WBDC_core, Receiver):
  """
  Wideband Downconverter Mod 1

  The down-converter accepts two Beam signals (each consisting of two
  polarization ComplexSignal signals).  It has two down-converters, each of
  which handles one Beam.

  WBDC1 monitor and control logic details are in spreadsheet ControlLogic
  in /usr/local/python/Observatory/Receivers/WBDC/doc.

  The class variable lists 'DC_names' and 'pol_names' will generate input port
  labels D1PA, D1PB, D2PA, D2PB in that order. With the class variable list
  'IF_names', the output port labels will be the above with either I1 or I2
  appended, in that order.
  """
  IF_names   = ["I1", "I2"]
  bands      = [22, 24]

  def __init__(self, name, inputs = None, output_names=None, active=True):
    """
    Initialize a WBDC1 object.

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
    self.logger.debug("initializing %s", self)
    self.logger.info(" %s inputs: %s", self, str(self.inputs))

    self.band = self.set_band()
    self.data['bandwidth'] = 2e9 # Hz
    self.logger.info(" %s outputs: %s", self, str(self.outputs))
    self._update_self()

  def set_band(self, band=22):
    assert contains(WBDC1.bands, band), \
      ("%s does not have band %d" % (self.name, band))
    self.data['frequency'] = band*1.e9
    self.band = band
    self._update_self()
    return self.band

  def get_band(self):
    return self.band

  def get_crossover(self):
    keys = self.Xswitch.keys()
    keys.sort()
    status = {}
    for key in keys:
      status[key] = self.Xswitch[key].get_state()
    return status

  def set_pol_mode(self,circular=False):
    for ch in self.pol_sec.keys():
      self.pol_sec[ch].set_pol_mode(circular)
    return self.get_pol_mode()

  def get_pol_mode(self):
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

  class DownConv(Receiver.DownConv):
    """
    Down-converter chain in a WBDC
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      """
      """
      self.logger = logging.getLogger(parent.logger.name+".DownConv")
      self.name = name
      self.logger.debug(" initializing %s", str(self))
      Receiver.DownConv.__init__(self, parent, name, inputs=inputs,
                                output_names=output_names, active=active)
      self.logger.debug(" %s inputs: %s", str(self), str(self.inputs))
      self.parent = parent
      self.channel = {}
      # The polarization into the DC channels depends on the state of the
      # polarization switch.  This means that it isn't necessarily the type
      # of polarization that came out of the switch, which is XY in the
      # Canberra K-band set-up.
      for pol in WBDC_base.out_pols:
        index = WBDC_base.out_pols.index(pol)
        inp = name+pol
        # pol = chlname[2:] # self.pols[index]
        self.logger.debug(" Processing %s channel %s for pol chl %s",
                          self, inp, pol)
        # the following collects the inputs with the same polarization
        pol_section_inputs = {}
        for key in self.inputs.keys():
          self.logger.debug(" Processing %s", key)
          self.logger.debug(" Signal pol is %s",
                            self.inputs[key].signal['pol'])
          if self.inputs[key].name[2:] == pol:
            pol_section_inputs[inp] = self.inputs[key]
        # the following generates the output names
        output_names = []
        for IF in WBDC_base.IF_names:
          ID = inp+IF
          output_names.append(ID)
        self.logger.debug("Chl %s outputs are %s", inp, output_names)
        self.channel[inp] = self.Channel(self, inp, pol=pol,
                                            inputs=pol_section_inputs,
                                            output_names=output_names)
        for nm in output_names:
          parent.outputs[nm] = self.outputs[nm]
      self.logger.debug(" %s outputs: %s", str(self), str(self.outputs))

    def set_IF_mode(self, SB_separated=False):
      keys = self.channel.keys()
      keys.sort()
      for key in keys:
        self.channel[key].set_IF_mode(SB_separated)
      if SB_separated:
        self.data['bandwidth'] = 1e9
      else:
        self.data['bandwidth'] = 2e9

    def get_IF_mode(self):
      keys = self.channel.keys()
      keys.sort()
      modes = {}
      for key in keys:
        modes[key] = self.channel[key].get_IF_mode()
      return modes

    def _update_self(self):
      self.logger.debug(" Updating %s", self)
      for inp in self.inputs.keys():
        self.inputs[inp].signal = copy.copy(self.inputs[inp].source.signal)
      keys = self.channel.keys()
      keys.sort()
      for key in keys:
        index = keys.index(key)
        pol = self.pols[index]
        self.channel[key].pol = pol
        self.channel[key]._update_self()

    class Channel(Receiver.DownConv.Channel):
      """
      Channel in a down-converter section of a WBDC

      Public attributes::
        signal - signal out of the polarization section for this channel
      """
      def __init__(self, parent, name, inputs=None, output_names=None,
                   active=True, pol=None):
        self.logger = logging.getLogger(parent.logger.name+".Channel")
        self.parent = parent
        self.name = name
        self.pol = pol
        self.logger.debug(" Initializing %s", self)
        Receiver.DownConv.Channel.__init__(self, parent, name, inputs=inputs,
                                  output_names=output_names, active=active)
        self.logger.debug(" %s inputs: %s", self, str(inputs))
        source = inputs[inputs.keys()[0]]
        self.set_IF_mode()
        for name in output_names:
          IFname = name[4:7]
          index = WBDC_base.IF_names.index(IFname)
          IFmode = self.IF_mode[index]
          self.outputs[name] = Port(self,name,
                                    source=source,
                                    signal=IF(source.signal, IFmode))
          self.parent.outputs[name] = self.outputs[name]
        self.logger.debug(" %s outputs: %s", self, str(self.outputs))
        self._update_self()

      def set_IF_mode(self, SB_separated=False):
        self.SB_separated = SB_separated
        if self.SB_separated:
          self.IF_mode = ["L","U"]
          self.data['bandwidth'] = 1e9
        else:
          self.IF_mode = ["I","Q"]
          self.data['bandwidth'] = 2e9
        self._update_self()
        return self.get_IF_mode()

      def get_IF_mode(self):
        return self.IF_mode

      def _update_self(self):
        self.logger.debug(" Updating %s inputs", self)
        for inp in self.inputs.keys():
          self.inputs[inp].signal = self.inputs[inp].source.signal
          self.inputs[inp].signal['pol'] = self.pol
          self.inputs[inp].signal.name = \
                                     self.inputs[inp].signal.name[:-1]+self.pol
        self.logger.debug(" Updating %s outputs", self)
        outkeys = self.outputs.keys()
        outkeys.sort()
        for key in outkeys:
          if self.outputs[key].signal:
            for prop in self.outputs[key].source.signal.keys():
              self.outputs[key].signal[prop] = \
                                          self.outputs[key].source.signal[prop]
            index = outkeys.index(key)
            self.outputs[key].signal.name = \
                       self.outputs[key].source.signal.name+self.IF_mode[index]
            self.outputs[key].signal['IF'] = self.IF_mode[index]
            self.outputs[key].signal['pol'] = self.pol
