"""
Module WBDC.WBDC2 provides class WBDC2
"""
import copy
import logging

from ... import IF, Port
from .. import Receiver
from . import WBDC_base
from .WBDC_core import WBDC_core
from support import contains

module_logger = logging.getLogger(__name__)

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
    WBDC_core.__init__(self, name, active=active, inputs=inputs,
                      output_names=output_names)
    self.logger = logging.getLogger(module_logger.name+".WBDC2")
    self.logger.debug(" initializing %s", self)
    self.logger.info(" %s inputs: %s", self, str(self.inputs))

    self.data['bandwidth'] = 2e9 # Hz

    # create transfer switch, which handles two pols
    self.Xswitch = self.TransferSwitch(self, "WBDC transfer switch",
                                       inputs=self.inputs,
                                       output_names = WBDC_base.RF_names)

    # This adds the method for actually controlling the switch
    switchIDs = self.Xswitch.keys()
    self.logger.debug(" Xswitch keys: %s", switchIDs)
    for ID in switchIDs:
      self.Xswitch[ID]._get_state = self.Xswitch.get_switch_state
      self.logger.debug(" Xswitch %s state: %s",
                        ID, self.Xswitch[ID].get_state())

    rfs = WBDC_base.RF_names
    rfs.sort()
    self.rf_sec = {}
    for rf in rfs:
      index = rfs.index(rf)
      rf_inputs = {}
      outnames = []
      for name in WBDC_base.pol_names:
        pindex = WBDC_base.pol_names.index(name)
        rf_inputs[rf+name] = self.Xswitch[name].outputs[rf+name]
        for band in self.band_names:
          outnames.append(rf+band+name)
      self.logger.debug("WBDC_base.__init__: RF inputs is now %s", rf_inputs)
      self.rf_sec[rf] = self.RFsection(self, rf, inputs = rf_inputs,
                                       output_names=outnames)
      self.logger.debug("WBDC_base.__init__: RF outputs is now %s",
                        self.rf_sec[rf].outputs)
                    
    self.pol_sec = {}
    for rf in rfs:
      pol_inputs = OrderedDict(sorted(self.rf_sec[rf].outputs.items()))
      self.logger.debug("WBDC_base.__init__: pol inputs is now %s",
                          pol_inputs)
      for band in WBDC2.bands:
        psec_inputs = {}
        for pol in WBDC_base.pol_names:
          psec_inputs[rf+band+pol] = pol_inputs[rf+band+pol]
        self.pol_sec[rf+band] = self.PolSection(self, rf+band,
                                                inputs = psec_inputs)
      self.logger.debug("WBDC_base.__init__: pol section %s outputs: %s",
              self.pol_sec[rf+band].name, self.pol_sec[rf+band].outputs.keys())
    pol_sec_names = self.pol_sec.keys()
    self.logger.debug("WBDC_base.__init__: pol sections: %s", pol_sec_names)

    self.DC = {}
    for name in pol_sec_names:
      for pol in WBDC_base.out_pols:
        self.logger.debug(" making DCs for %s", name+pol)
        self.logger.debug(" creating inputs for %s", name+pol)
        dc_inputs = {name+pol: self.pol_sec[name].outputs[name+pol]}
        self.DC[name+pol] = self.DownConv(self, name+pol,
                                          inputs = dc_inputs)
        self.DC[name+pol].set_IF_mode() # default is IQ
        self.logger.debug(" DC %s created", self.DC[name+pol])
    # report outputs
    self.logger.info(" %s outputs: %s",
                     self, str(self.outputs))
    self._update_self()
    self.logger.debug(" initialized for %s", self.name)

    # Report outputs
    self.logger.info(" %s outputs: %s", self, str(self.outputs))

  def get_crossover(self):
    """
    Get the state of the beam cross-over switches
    """
    keys = self.Xswitch.keys()
    self.logger.debug("get_crossover: checking switches %s", keys)
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
    
  class TransferSwitch(WBDC_core.TransferSwitch):
    """
    Beam to down-converter transfer switch

    There is one Switch object for each front-end polarization P1 and P2.

    At some point this might become a general transfer switch class
    """
    def __init__(self, parent, name, inputs=None, output_names=None):
      self.name = name
      WBDC_core.TransferSwitch.__init__(self, parent, name, inputs=inputs,
                                        output_names=output_names)
      self.logger = logging.getLogger(parent.logger.name+".TransferSwitch")
      self.logger.debug(" initializing %s", self)
      self.logger.info(" %s inputs: %s", self, str(self.inputs))
      self.parent = parent

  class RFsection(WBDC_core.RFsection):
    """
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      self.parent = parent
      WBDC_core.RFsection.__init__(self, parent, name, inputs=inputs,
                                  output_names=output_names, active=True)
      self.logger = logging.getLogger(parent.logger.name+".RFsection")
      self.logger.debug(" initializing WBDC2 %s", self)
      self.logger.info(" %s inputs: %s", self, str(self.inputs))
      self.logger.info(" %s outputs: %s", self, str(self.outputs))

    def hello(self):
      print self.logger.name, "says 'Hello'"

    def _update_outputs(self):
      keys = self.outputs.keys()
      keys.sort()
      for key in keys:
        # The 
        self.outputs[key] = Port(self, key,
                                 source=self.source,
                                 signal=self.source.signal)
         
  class PolSection(WBDC_core.PolSection):
    """
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      WBDC_core.PolSection.__init__(self, parent, name, inputs=inputs,
                                  output_names=output_names,
                                  active=active)
      self.logger = logging.getLogger(parent.logger.name+".PolSection")
      self.logger.debug(" __init__: output names: %s",
                        output_names)
      self.logger.debug(" initializing WBDC2 %s", self)
      self.logger.info(" %s inputs: %s", self, str(self.inputs))
      self.logger.info(" %s outputs: %s", self, str(self.outputs))

  class DownConv(WBDC_base.DownConv):
    """
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      WBDC_base.DownConv.__init__(self, parent, name, inputs=inputs,
                                 output_names=output_names,
                                 active=active)
      self.logger = logging.getLogger(parent.logger.name+".DownConv")

############################### no longer used ###########################

  class xDownConv(WBDC_base.DownConv):
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
        for IF in WBDC2.IF_names:
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
