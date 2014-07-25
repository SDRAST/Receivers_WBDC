"""
WBDC - module for Wide Band Down Converter receiver classes

Overview
--------
The prototype WBDC has two inputs, each producing two orthogonal linear
polarizations.  There are two down-converter chains, each handling two
polarizations, for a total of four signals.

There are two versions of the wideband down-converter. WBDC1 has two RF
sections after the band-splitting filters, one for 22 and 24 GHz, two
switch-selectable LOs and one IF section.  WBDC2 has five RF sections and five
IF sections.  The sections, as well as feed switching, polarization selection,
etc. are the same.

Input Switching
---------------
The first stage of the WBDC allows the down-converter groups to be switched
between the two feeds.

Polarization Conversion
-----------------------
After the band-selecting RF filters, the linearly polarized signals from each
feed can be switched into a quadrature hybrid to be converted to cicular
polarizations.

Sideband Separation
-------------------
The down-conversion produces complex outputs (i.e. a pair of signals I and
Q).  There are switches which can direct each I/Q pair into a quadrature
hybrid to convert them to an upper and lower sideband pair.
"""
import logging
import copy

from MonitorControl import Device, Switch, Port, IF,  ObservatoryError
from MonitorControl.Receivers import Receiver
from support import unique

class WBDC_base(Receiver):
  """
  Base class for a DSN K-band wideband down-converter

  The DSN K-band WBDC systems have two dual polarization feeds. The feeds
  can be interchanged with a pair of transfer switches
  """
  pol_names  = ["P1", "P2"]
  RF_names   = ["R1", "R2"]
  out_pols   = ["PA", "PB"]
  DC_names   = ["D1", "D2"]
  IF_names   = ["I1", "I2"]
  
  def __init__(self, name, inputs=None, output_names=None, active=True):
    """
    Initialize a physical WBDC object.

    @param name : unique identifier
    @type  name : str

    @param inputs : a dict with sources for different inputs
    @type  inputs : dict of str:str

    @param output_names : names of the output channels/ports
    @type  output_names : list of str

    @param active : True is the FrontEnd instance is functional
    @type  active : bool
    """
    Receiver.__init__(self, name, active=active, inputs=inputs,
                      output_names=output_names)
    self._create_keys(inputs)
    # create transfer switch
    self.Xswitch = self.TransferSwitch(self, "WBDC transfer switch",
                                       inputs=self.inputs,
                                       #output_names = WBDC_base.DC_names)
                                       output_names = WBDC_base.RF_names)
    # create two RF and two pol sections
    self.rf_sec = {}
    self.pol_sec = {}
    rfs = WBDC_base.RF_names
    rfs.sort()
    for rf in rfs:
      rf_inputs = {}
      for name in WBDC_base.pol_names:
        rf_inputs[rf+name] = self.Xswitch[name].outputs[rf+name]
      self.rf_sec[rf] = self.RFsection(self, rf, inputs = rf_inputs)
      self.pol_sec[rf] = self.PolSection(self, rf, inputs = rf_inputs)
    # get the new
    # create DCs
    self.DC = {}
    dcs = WBDC_base.DC_names
    dcs.sort()
    for dc in dcs:
      rf_name = "R"+dc[1]
      dc_inputs = {}
      for name in WBDC_base.out_pols:
        dc_inputs[dc+name] = self.pol_sec[rf_name].outputs[rf_name+name]
      self.DC[dc] = self.DownConv(self, dc, inputs = dc_inputs)   
    self.logger.info(" %s outputs: %s", self, str(self.outputs))
    self._update_self()
    
  def _create_keys(self,inputs):  
    """
    Create sorted lists of input, beam, and polarization names
    """
    self.inkeys = inputs.keys()
    self.inkeys.sort()
    self.beams = []
    self.pols = []
    for key in self.inkeys:
      self.beams.append(inputs[key].signal['beam'])
      self.pols.append(inputs[key].signal['pol'])
    self.beams = unique(self.beams)
    self.beams.sort()
    self.pols = unique(self.pols)
    self.pols.sort()

  def _update_self(self):
    self.logger.debug(" updating %s", self)
    self.Xswitch._update_self()
    keys = self.outputs.keys()
    keys.sort()
    try:
      for key in self.DC.keys():
        self.DC[key]._update_self()
    except AttributeError:
      pass

  def set_crossover(self, crossed=False):
    keys = self.Xswitch.keys()
    keys.sort()
    for sw in keys:
      self.Xswitch[sw].set_state(int(crossed))
      for name in self.outputs.keys():
        for prop in self.outputs[name].source.signal.keys():
          for destination in self.outputs[name].destinations:
            destination.signal[prop] = self.outputs[name].signal[prop]
    self._update_self()
    return self.get_crossover()
    
  class TransferSwitch(Device):
    """
    Beam to down-converter transfer switch

    There is one Switch object for each front-end polarization P1 and P2.

    At some point this might become a general transfer switch class
    """
    def __init__(self, parent, name, inputs=None, output_names=None):
      self.name = name
      Device.__init__(self, name)
      self.logger.debug("initializing %s", self)
      self.logger.info(" %s inputs: %s", self, str(self.inputs))
      # This directs the polarizations to the down-converters according
      # to ordered lists defined in WBDC_base
      for pol in parent.pols:
        index = parent.pols.index(pol)
        pol_num = index+1
        pol_ID = "P"+str(pol_num) # WBDC_base.pol_names[index]
        pol_inputs = {}
        for key in parent.inkeys:
          if parent.inputs[key].signal['pol'] == pol:
            pol_inputs[key] = inputs[key]
        self.data[pol_ID] = Switch(self, pol_ID,
                               inputs = pol_inputs,
                               output_names = [output_names[0]+pol_ID,
                                               output_names[1]+pol_ID],
                               stype = "2x2")
      self.logger.info(" %s outputs: %s", self, str(self.outputs))

    def set_crossover(self, crossed=False):
      self.Xswitch.set_crossover(crossed=crossed)
      self._update_self()
      return self.Xswitch.get_crossover()

    def get_crossover(self):
      return self.Xswitch.get_crossover()

    def _update_self(self):
      for key in self.data.keys():
        self.data[key]._update_self()
                                     
  class RFsection(Receiver.RFsection):
    """
    An RF section may split the signal into several sub-bands.

    WBDC2 will need channels.  For now this is coded for WBDC1 which only
    narrows the bandwidth from 17-27 GHz to 21-25 GHz.
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      """
      The default RF section just passes the signals through
      """
      Receiver.RFsection.__init__(self, parent, name, inputs=None,
                                  output_names=None, active=True)
      self.logger.debug("initializing %s", self)
      self.logger.info(" %s inputs: %s", self, str(self.inputs))
      output_names = inputs.keys()
      output_names.sort()
      Receiver.RFsection.__init__(self, parent, name, inputs=inputs,
                                  output_names=output_names, active=active)
      self.logger.info(" %s outputs: %s", self, str(self.outputs))
      self._update_self()

    def _update_self(self):
      """
      """
      for key in self.inputs.keys():
        self.inputs[key].signal = copy.copy(self.inputs[key].source.signal)
        self.outputs[key].signal = copy.copy(self.inputs[key].signal)
        self.outputs[key].signal['frequency'] = 23 # GHz
        self.outputs[key].signal['bandwidth'] = 4 # GHz

  class PolSection(Receiver.PolSection):
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      Receiver.PolSection.__init__(self, parent, name, inputs=None,
                                   output_names=None, active=True)
      self.logger.debug("initializing %s", self)
      self.logger.info(" %s inputs: %s", self, str(self.inputs))
      self.output_names = []
      for pname in WBDC_base.out_pols:
        self.output_names.append(name+pname)
      self.output_names.sort()
      Receiver.PolSection.__init__(self, parent, name, inputs=inputs,
                                  output_names=self.output_names,
                                  active=active)
      self.set_pol_mode() # defaults to X,Y
      self.logger.info(" %s outputs: %s", self, str(self.outputs))
      self._update_self()

    def set_pol_mode(self,circular=False):
      self.circular = circular
      if self.circular:
        self.pols = ["L", "R"]
      else:
        self.pols = ["X", "Y"]
      self._update_self()

    def get_pol_mode(self):
      return self.circular

    def _update_self(self):
      """
      """
      input_keys = self.inputs.keys()
      input_keys.sort()
      for key in input_keys:
        self.inputs[key].signal = copy.copy(self.inputs[key].source.signal)
        outkey = self.output_names[input_keys.index(key)]
        self.outputs[outkey].signal = copy.copy(self.inputs[key].signal)
        pol_index = int(key[-1])-1
        self.outputs[outkey].signal['pol'] = self.pols[pol_index]

  class DownConv(Receiver.DownConv):
    def __init__(self):
      pass
