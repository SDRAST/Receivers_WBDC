"""
Module WBDC.WBDC2 provides class to interface to WBDC2 hardware server

Overview
========

For a description of the generic Wide Band Down Converter see/do
MonitorControl.Receivers.WBDC.__doc__.split('\n')

WBDC2 has two signal input pairs, each accepting two orthogonal linear
polarizations. There are two down-converter chains, each handling two
polarizations each, for a total of four complex signals.

Monitor and control is done with LabJacks. For a detailed description of
the use of LabJacks see the WBDC2hwif module documentation.

Motherboard Monitoring
======================

Digital Module 1
----------------

Seven latch groups are assigned to digital monitoring, that is, the program
reads the latch states.  For detailed information see the WBDC2hwif module
documentation.


Digital Module 2
----------------

Latch Groups 1-4
~~~~~~~~~~~~~~~~
Receiver chain 1 IQ hybrids are monitored by high address latch groups 1 and 2.
Receiver chain 2 IQ hybrids are monitores by high address latch groups 3 and 4.
For detailed information see the WBDC2hwif module documentation.

Latch LEDs
~~~~~~~~~~
The LEDs at the top right of the motherboard can only be seen when the receiver
lid is open so this is of little interest to the observer.  For detailed
information see the WBDC2hwif module documentation.

Analog Monitoring
-----------------

Latch 1
~~~~~~~
This latch selects voltage and current monitoring points.  Voltage points are
selected using bits 0-2 and read at AIN1.  Currents are selected using bits
3-6 and read at AIN0.

The voltages which can be monitored are::
 0 ---- 000  +6 V digital
 0 ---- 001  +6 V analog
 0 ---- 010 +16 V DC
 0 ---- 011 +12 V DC
 0 ---- 100 -16 V DC

Typical currents::
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

Latch 2
~~~~~~~
This latch selects temperatures and RF detector voltages.

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
"""
import copy
import logging
import re
from collections import OrderedDict
import os.path

import Math
from MonitorControl import ComplexSignal, Device, IF, Port, ObservatoryError
from MonitorControl import show_port_sources
from MonitorControl.Receivers import Receiver
from MonitorControl.Receivers.WBDC import WBDC_base
from support.lists import contains
from support.pyro import get_device_server, pyro_server_request
from support.test import auto_test

logger = logging.getLogger(__name__)
package_dir = "/usr/local/lib/python2.7/DSN-Sci-packages/"
module_subdir = "MonitorControl/Receivers/WBDC/WBDC2/"

def show_signal(parent, ports):
  """
  Diagnostic tool
  """
  inkeys = ports.keys()
  test = ports[inkeys[0]]
  logger.debug("show_signal: %s %s signal is %s",parent, test, test.signal)
  sigkeys = test.signal.keys()
  for key in sigkeys:
    logger.debug("show_signal:  %s = %s", key, test.signal[key])

class WBDC2(WBDC_base, Receiver):
  """
  Wideband Downconverter Mod 2 client

  The down-converter accepts two Beam class signals (each consisting of two
  polarization ComplexSignal signals).  It has two down-converters, each of
  which handles one Beam.

  WBDC2 monitor and control logic details are in spreadsheet ControlLogic
  in /usr/local/python/Observatory/Receivers/WBDC/doc.

  The class variable lists 'DC_names' and 'pol_names' match input port
  labels D1PA, D1PB, D2PA, D2PB in that order. With the class variable list
  'IF_names', the output port labels are labelle with either I1 or I2
  appended, in that order.
  """
  bands      = ["18", "20", "22", "24", "26"]

  def __init__(self, name, inputs=None, output_names=None, active=True,
               hardware=None):
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
    if hardware:
      from support.pyro import get_device_server, pyro_server_request
      self.hardware = get_device_server("wbdc2hw_server-dss43wbdc2",
                                        pyro_ns="crux")
      self.atten_keys = pyro_server_request(self.hardware.get_atten_IDs)
    else:
      self.hardware = None
    mylogger = logging.getLogger(logger.name+".WBDC2")
    mylogger.debug("__init__: for %s", self)
    show_port_sources(inputs, "WBDC2.__init__: inputs before WBDC_base init:",
                        mylogger.level)
    WBDC_base.__init__(self, name,
                       active=active,
                       inputs=inputs,
                       output_names=output_names)
    if inputs is not None:
        show_port_sources(self.inputs, "WBDC2.__init__: inputs after WBDC_base init:",
                        mylogger.level)

    show_port_sources(self.outputs, "WBDC2.__init__: outputs after WBDC_base init:",
                        mylogger.level)
    self.logger = mylogger

    self.data['bandwidth'] = 1e10 # Hz

    # The transfer switch is created in WBDC_base
    if self.hardware:
      self.crossSwitch.get_state()
    else:
      self.crossSwitch.set_state(False)

    # the four transfer switch outputs (2 feeds, 2 pols) are RF section inputs
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
      self.logger.debug(" __init__: RF %s outputs is now %s\n",
                        rf, self.rf_section[rf].outputs)

    # Outputs from two RFsections for each feed and band feed a pol section
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
    self.logger.debug(" __init__: pol sections: %s\n", pol_sec_names)

    # Each pol section has two outputs, each going to a down-converter
    # Each down-converter has two IF outputs
    self.DC = {}
    for name in pol_sec_names:
      for pol in WBDC_base.out_pols:
        self.logger.debug("__init__: making DC for %s", name+pol)
        self.logger.debug("__init__: creating inputs for %s", name+pol)
        dc_inputs = {name+pol: self.pol_sec[name].outputs[name+pol]}
        self.DC[name+pol] = self.DownConv(self, name+pol,
                                          inputs = dc_inputs)
        rx,band = name.split('-')
        self.DC[name+pol].data['receiver'] = rx
        self.DC[name+pol].data['band'] = band
        self.DC[name+pol].data['pol'] = pol
        self.DC[name+pol]._get_state()
        self.logger.debug("__init__: DC %s created", self.DC[name+pol])
    self._update_signals() # invokes WBDC_base._update_signals()
    # debug outputs
    self.logger.debug("__init__: %s outputs: %s",
                     self, str(self.outputs))

    self.analog_monitor = self.AnalogMonitor(self)
    self.logger.debug(" initialized for %s", self.name)

  # cross-over switch
  @auto_test()
  def set_crossover(self, crossover):
    """
    Set or unset the crossover switch
    """
    if self.hardware:
      response = self.hardware.set_crossover(crossover)
    else:
      response = crossover
    self.crossSwitch.state = self.get_crossSwitch.state
    return self.crosssSwitch.state

  @auto_test()
  def get_crossover(self):
    """
    Set or unset the crossover switch
    """
    if self.hardware:
      return self.hardware.get_crossover(crossover)
    else:
      return self.crossSwitch.state

  # polarization sections

  @auto_test()
  def set_pol_modes(self, circular=False):
    """
    Set all polarization sections to the specified mode; default: linear
    """
    status = {}
    keys = self.pol_sec.keys()
    keys.sort()
    for key in self.pol_sec.keys():
      status[key] = self.pol_sec[key].set_state(circular)
    return status

  @auto_test()
  def get_pol_modes(self):
    """
    Get the modes of all the polarization sections
    """
    status = {}
    keys = self.pol_sec.keys()
    keys.sort()
    for key in self.pol_sec.keys():
      status[key] = self.pol_sec[key].get_state()
    return status

  # polarizer section attenuators

  @auto_test()
  def get_atten_IDs(self):
    """
    Returns the names of all the RF attenuators in the pol sections

    Should not be needed as this is done when the remote object is initialized.
    """
    if self.hardware:
      self.atten_keys = self.hardware.get_atten_IDs()
    else:
      self.atten_keys = []
    return self.atten_keys

  @auto_test()
  def set_atten_volts(self, ID, V):
    """
    Set the control voltage of a specified attenuator
    """
    if self.hardware:
      return self.hardware.set_atten_volts(ID, V)
    else:
      return False

  @auto_test()
  def get_atten_volts(self, ID):
    """
    Get the control voltage of a specified attenuator
    """
    if self.hardware:
      return self.hardware.get_atten_volts(ID)
    else:
      return 0.0

  @auto_test()
  def set_atten(self, ID, dB):
    """
    Sets pol section quad hybrid input attentuator
    """
    if self.hardware:
      return self.hardware.set_atten(ID, dB)
    else:
      return -20

  @auto_test()
  def get_atten(self, ID):
    """
    Returns the attenuation to which the specified attenuator is set.

    This does not query the hardware.  The attenuator simply remembers the last
    requested attenuation.  If 'set_atten' has not been used, it rteurns a
    blank.
    """
    if self.hardware:
      return self.hardware.get_atten(ID)
    else:
      return -20

  # down-converter sections

  @auto_test()
  def set_IF_modes(self, SB_separated=False):
    """
    Set the IF mode of all the down-converters
    """
    for key in self.DC.keys():
      self.DC[key].set_IF_(SB_separated)
    if SB_separated:
      self.data['bandwidth'] = 1e9
    else:
      self.data['bandwidth'] = 2e9
    return self.get_IF_mode()

  @auto_test()
  def get_IF_modes(self):
    """
    Get the IF mode of all the down-converters
    """
    modes = {}
    keys = self.DC.keys()
    keys.sort()
    for key in self.DC.keys():
      modes[key] = self.DC[key].get_state()
    return modes

  @auto_test()
  def get_monitor_data(self):
    """
    Returns the analog voltages, currents and temperatures
    """
    if self.hardware:
      return self.hardware.get_monitor_data()
    else:
      return {}

  @auto_test()
  def set_polarizers(self, state):
    """
    Set all polarizers to the specified state

    True for E/H to L/R conversion.  Flase for bypass.
    """
    if self.hardware:
      self.hardware.set_polarizers(state)
      return self.hardware.get_polarizers()
    else:
      for key in self.pol_sec.keys():
        self.pol_sec[key].state = state
      return self.get_polarizers()

  @auto_test()
  def get_polarizers(self):
    """
    Set all polarizers to the specified state

    True for E/H to L/R conversion.  Flase for bypass.
    """
    if self.hardware:
      return self.hardware.get_polarizers()
    else:
      response = {}
      for key in self.pol_sec.keys():
        response[key] = self.pol_sec[key].state
      return response

  @auto_test()
  def sideband_separation(self, state):
    """
    Convert I/Q to LSB/USB

    When a hybrid state is 1 or True, the hybdrids are bypassed.  This is the
    default (on power up) state.  When the state is 0 or False, the hybrid is
    engaged to convert the complex IF (I and Q) to lower and upper sidebands.

    To make this function more intuitive, the logic is inverted here, that is,
    True means that the sidebands are separated.
    """
    if self.hardware:
      states = self.hardware.sideband_separation(state)
    return self.get_IF_hybrids()

  @auto_test()
  def get_IF_hybrids(self):
    """
    Returns the state of the IQ-to-LU hybrids.

    True means that the hybrid is bypassed, False that it is engaged.
    """
    if self.hardware:
      states = self.hardware.get_IF_hybrids()
    else:
      states = {}
      for key in self.DC.keys():
        states[key] = self.DC[key].get_state()
    return states


  class TransferSwitch(WBDC_base.TransferSwitch):
    """
    Beam to down-converter transfer switch

    There is one Switch object for each front-end polarization P1 and P2.


    At some point this might become a general transfer switch class
    """
    def __init__(self, parent, name, inputs=None, output_names=None):
      mylogger = logging.getLogger(logger.name+".WBDC2.TransferSwitch")
      self.name = name
      self.parent = parent
      self.hardware = self.parent.hardware
      WBDC_base.TransferSwitch.__init__(self, parent, name, inputs=inputs,
                                        output_names=output_names)
      mylogger.debug("__init__: for %s", self)
      if hasattr(self, "inputs"):
          mylogger.debug("__init__: %s inputs: %s", self, str(self.inputs))
      self.logger = mylogger
      self.logger.debug("__init__: %s outputs: %s\n", self, str(self.outputs))

    def set_state(self, state):
      """
      Set the state of the beam cross-over switches
      """
      keys = self.data.keys()
      self.logger.debug(
                  "get_state: checking switches %s", keys)
      if self.hardware:
        self.state = self.hardware.set_crossover(state)
      else:
        self.state = state
      return self.get_state()

    def get_state(self):
      """
      Get the state of the beam cross-over switches
      """
      keys = self.data.keys()
      self.logger.debug(
                  "get_state: checking switches %s", keys)
      if self.hardware:
        self.state = self.hardware.get_crossover()
      return self.state

    class Xswitch(WBDC_base.TransferSwitch.Xswitch):
      """
      """
      def __init__(self, parent, name, inputs=None, output_names=None,
                   active=True):
        self.name = name
        self.parent = parent
        self.hardware = self.parent.hardware
        mylogger = logging.getLogger(logger.name+"WBDC2.TransferSwitch.Xswitch")
        WBDC_base.TransferSwitch.Xswitch.__init__(self, parent, name,
                                                  inputs=inputs,
                                                  output_names=output_names,
                                                  active=active)

      def _get_state(self):
        """
        Get the state from the hardware switch.
        """
        self.logger.debug("_get_state:  for %s", self)
        if self.hardware:
          self.state = self.hardware.get_Xswitch_state(self.name)
        return self.state

  class RFsection(WBDC_base.RFsection):
    """
    An RF section converts a polarized front-end signal to a Complex RF signal
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      """
      """
      self.parent = parent
      self.name = name
      mylogger = logging.getLogger(logger.name+".WBDC2.RFsection")
      mylogger.debug("__init__: for WBDC2 %s", self)
      show_port_sources(inputs,
           "WBDC2.RFsection.__init__: inputs before WBDC_base.RFsection init:",
           mylogger.level)
      self.inputs = inputs
      WBDC_base.RFsection.__init__(self, parent, name, inputs=inputs,
                                  output_names=output_names, active=True)
      show_port_sources(self.inputs,
            "WBDC2.RFsection.__init__: inputs after WBDC_base.RFsection init:",
                        mylogger.level)
      show_port_sources(self.outputs,
           "WBDC2.RFsection.__init__: outputs after WBDC_base.RFsection init:",
                        mylogger.level)
      self.logger = mylogger
      self._update_signals()

    def _update_signals(self):
      """
      Update the signals at the outputs
      """
      self.logger.debug("_update_signals: updating %s", self.name)
      # connect the ports
      self._connect_ports()
      # update the signals
      outnames = self.outputs.keys()
      outnames.sort()
      for key in self.inputs.keys():
        if hasattr(self.inputs[key].signal,'copy'):
          self.logger.debug("_update_signals: processing input port %s", key)
          self.inputs[key].signal.copy(self.inputs[key].source.signal)
          for outkey in outnames:
            self.outputs[outkey].signal = ComplexSignal(self.inputs[key].signal)
            self.outputs[outkey].signal.name = outkey
            self.logger.debug(" _update_signals: output port %s signal is %s",
                              outkey, self.outputs[outkey].signal)
            self.outputs[outkey].signal['bandwidth'] = 2 # GHz
            self.outputs[outkey].signal['frequency'] = float(outkey[-2:])

  class PolSection(WBDC_base.PolSection):
    """
    Class for optional conversion of E,H pol to L,R and attenuators adjustment.

    The attenuator assignment is as follows::
      PolSec  Pol DAC
      Rx-18    H   A
               E   B
      Rx-20    H   A
               E   B
      Rx-22    H   A
               E   B
      Rx-24    H   A
               E   B
      Rx-26    H   A
               E   B
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      """
      """
      mylogger = logging.getLogger(logger.name+".WBDC2.PolSection")
      self.name = name
      self.parent = parent
      self.hardware = self.parent.hardware
      mylogger.debug("__init__: for %s", self)
      WBDC_base.PolSection.__init__(self, parent, name, inputs=inputs,
                                  output_names=output_names,
                                  active=active)
      self.logger = mylogger
      self.logger.debug("__init__: %s inputs: %s", self, str(self.inputs))
      self.logger.debug("__init__: %s output names: %s", self, output_names)
      inkeys = self.inputs.keys()
      inkeys.sort()
      self.atten = {}
      for key in inkeys:
        att_name = self.name+'-'+key
        self.logger.debug("__init__: creating attenuator %s", att_name)
        self.atten[att_name] = self.IFattenuator(self, att_name)
      outkeys = self.outputs.keys()
      outkeys.sort()
      for key in outkeys:
        indx = outkeys.index(key)
        inname = inkeys[indx]
        # A pol section does not change the signal type
        self.outputs[key] = Port(self, key,
                                 source=self.inputs[inname],
                         signal=ComplexSignal(self.inputs[inname].signal))
      self.logger.debug("__init__: %s outputs: %s", self, str(self.outputs))
      self.update_signals()

    def _get_state(self):
      """
      Returns the state of the polarization conversion section.

      X,Y are converted to L,R if the state is 1.

      The pol section needs to know what band it belongs to to know what
      latches to use.  If that isn't available, return the default.
      """
      if self.hardware:
        self.hardware.get_polarizer(self.name)
      return self.state

    def _set_state(self,state):
      """
      Sets the state of the polarization conversion section.

      If set, E,H are converted to L,R.

      The pol section needs to know what band it belongs to to know what
      latches to use.
      """
      if self.hardware:
        self.hardware.set_polarizer(self.name, state)
      else:
        self.state = state
      try:
        self.update_signals()
      except AttributeError:
        # ignore if output signals have not yet been defined
        pass
      return self.state

    class IFattenuator():   #   (PINattenuator)
      """
      """
      def __init__(self, parent, name):
        """
        """
        self.parent = parent
        self.name = name
        self.hardware = self.parent.hardware
        mylogger = logging.getLogger(
                                   logger.name+"WBDC2.PolSection.IFattenuator")
        mylogger.debug("__init__: for %s and parent %s", self, parent)
        self.logger = mylogger

      def set_atten_volts(self, ID, V):
        """
        Sets the designated attenuator voltage
        """
        if self.hardware:
          self.hardware.set_atten_volts(ID, V)
        return self.get_atten_volts(ID)

      def get_atten_volts(ID):
        """
        Gets the designated attenuator voltage
        """
        if self.hardware:
          return self.hardware.get_atten_volts(ID)
        else:
          return 0.0

      def set_atten(self, ID, dB):
        """
        Sets pol section quad hybrid input attentuator

        @param ID : attenuator identifier
        @type  ID : str

        @param atten : requested attenuation
        @type  atten : float
        """
        if self.hardware:
          self.hardware.set_atten(ID, dB)
        self.get_atten(ID)

      def get_atten(self, ID):
        """
        Gets pol section quad hybrid input attentuator

        @param ID : attenuator identifier
        @type  ID : str

        @param atten : requested attenuation
        @type  atten : float
        """
        if self.hardware:
          self.hardware.get_atten(ID)
        else:
          return -20

  class DownConv(WBDC_base.DownConv):
    """
    Converts RF to IF

    A hybrid optional converts the I and Q IFs to LSB and USB.
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      """
      """
      mylogger = logging.getLogger(parent.logger.name+".DownConv")
      self.name = name
      self.parent = parent
      self.hardware = self.parent.hardware
      mylogger.debug("__init__: for %s", self)
      show_signal(self, inputs)
      WBDC_base.DownConv.__init__(self, parent, name, inputs=inputs,
                                 output_names=output_names,
                                 active=active)
      if self.hardware:
        self.hardware.set_DC_state(default)
      super(WBDC_base.DownConv, self).set_state() # default is bypass
      self.logger = mylogger
      keys = self.outputs.keys()
      keys.sort()
      self.logger.debug("__init__: outputs: %s", keys)
      for key in keys:
        IFname = key[-2:]
        index = WBDC_base.IF_names.index(IFname)
        IFmode = self.get_state()
        self.logger.debug("__init__: %s IF mode is %s", key, IFmode)
        self.outputs[key] = Port(self, key,
                       source=self.outputs[key].source,
                    signal=IF(self.outputs[key].source.signal, IF_type=IFmode))
        self.parent.outputs[key] = self.outputs[key]

    def _get_state(self):
      """
      """
      if self.hardware:
        self.state = self.hardware.get_IF_hybrid_state()
      return self.state

    def _set_state(self, state):
      """
      """
      if self.hardware:
        self.hardware.set_IF_hybrid_state(state)
      else:
        self.state = state
      try:
        self._update_signals()
      except AttributeError:
        # ignore if the output port signals have not yet beed defined.
        pass
      return self.state

  class AnalogMonitor():
    """
    """
    def __init__(self, parent):
      """
      """
      self.parent=parent
      mylogger = logging.getLogger(self.parent.logger.name+".AnalogMonitor")
      self.logger = mylogger

if __name__ == "__main__":
  """
  Tests class WBDC2 in configuration
  """
  from MonitorControl.config_test import show_signal_path
  from MonitorControl.Configurations import station_configuration
  from MonitorControl.Configurations.CDSCC.WBDC2_K2 import IFswitch
  from MonitorControl.config_test import show_signal_path

  testlogger = logging.getLogger()
  testlogger.setLevel(logging.DEBUG)

  lab,equipment = station_configuration("WBDC2_K2")
  show_signal_path([equipment['FrontEnd'],
                    equipment['Receiver'],
                    equipment['IF_switch'],
                    equipment['Backend']])
