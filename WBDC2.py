"""
Module WBDC.WBDC2 provides class WBDC2
"""
import copy
import logging
from collections import OrderedDict

from ... import ComplexSignal, IF, Port
from .. import Receiver
from . import WBDC_base
from .WBDC_core import WBDC_core
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
    show_signal(self,inputs)
    WBDC_core.__init__(self, name, active=active, inputs=inputs,
                      output_names=output_names)
    show_signal(self,inputs)                  
    self.logger = logging.getLogger(module_logger.name+".WBDC2")
    self.logger.debug(" initializing %s", self)
    self.logger.info(" %s inputs: %s", self, str(self.inputs))

    self.data['bandwidth'] = 2e9 # Hz

    # create transfer switch, which handles two pols
    self.Xswitch = self.TransferSwitch(self, "WBDC transfer switch",
                                       inputs=inputs,
                                       output_names = WBDC_base.RF_names)
    # This adds the method for actually controlling the switch
    switchIDs = self.Xswitch.keys()
    self.logger.debug(" Xswitch keys: %s", switchIDs)
    for ID in switchIDs:
      self.Xswitch[ID]._get_state= lambda: self.Xswitch.get_subswitch_state(ID)
      self.logger.debug(" Xswitch %s state: %s",
                        ID, self.Xswitch[ID].get_state())
    self.Xswitch.get_state()
    
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
        for band in WBDC2.bands:
          outnames.append(rf+band+name)
      self.logger.debug(" __init__: RF inputs is now %s", rf_inputs)
      self.rf_sec[rf] = self.RFsection(self, rf, inputs = rf_inputs,
                                       output_names=outnames)
      self.logger.debug(" __init__: RF outputs is now %s",
                        self.rf_sec[rf].outputs)
                    
    self.pol_sec = {}
    for rf in rfs:
      pol_inputs = OrderedDict(sorted(self.rf_sec[rf].outputs.items()))
      self.logger.debug(" __init__: pol inputs is now %s",
                          pol_inputs)
      for band in WBDC2.bands:
        psec_inputs = {}
        for pol in WBDC_base.pol_names:
          psec_inputs[rf+band+pol] = pol_inputs[rf+band+pol]
        self.pol_sec[rf+band] = self.PolSection(self, rf+band,
                                                inputs = psec_inputs)
        self.logger.debug(" __init__: pol section %s outputs: %s",
              self.pol_sec[rf+band].name, self.pol_sec[rf+band].outputs.keys())
    pol_sec_names = self.pol_sec.keys()
    self.logger.debug(" __init__: pol sections: %s", pol_sec_names)

    self.DC = {}
    for name in pol_sec_names:
      for pol in WBDC_base.out_pols:
        self.logger.debug(" making DC for %s", name+pol)
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
      self.logger = logging.getLogger(module_logger.name+".TransferSwitch")
      self.logger.debug(" initializing %s", self)
      self.logger.info(" %s inputs: %s", self, str(self.inputs))
      self.parent = parent

    def set_state(self, crossover=False):
      """
      """
      return super(WBDC2.TransferSwitch,self).set_crossover(crossover=crossover)
        
    def get_state(self):
      """
      Get the state of the beam cross-over switches
      """
      keys = self.data.keys()
      self.logger.debug("get_state: checking switches %s", keys)
      return super(WBDC2.TransferSwitch,self).get_crossover()

  class RFsection(WBDC_core.RFsection):
    """
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      self.parent = parent
      self.name = name
      show_signal(self, inputs)
      WBDC_core.RFsection.__init__(self, parent, name, inputs=inputs,
                                  output_names=output_names, active=True)
      self.logger = logging.getLogger(module_logger.name+".RFsection")
      self.logger.debug(" initializing WBDC2 %s", self)
      self.logger.info(" %s inputs: %s", self, str(self.inputs))
      self.logger.info(" %s outputs: %s", self, str(self.outputs))
      self._update_outputs()
      self._update_self()

    def _update_outputs(self):
      for key in self.outputs.keys():
        # The RF section does not change the signal type but makes sub-bands
        self.outputs[key] = Port(self, key,
                                 source=self.outputs[key].source,
                   signal=ComplexSignal(self.outputs[key].source.signal))
        
    def _update_self(self):
      """
      """
      self.logger.debug(" _update_self: updating %s",
                        self.name)
      # connect the ports
      self._propagate()
      # update the signals
      for key in self.inputs.keys():
        self.logger.debug(
                        " _update_self: processing input port %s",
                        key)
        self.inputs[key].signal.copy(self.inputs[key].source.signal)
        #if self.parent.band_names:
        for band in WBDC2.bands:
          outkey = key[:2]+band+key[2:]
          #copy.deepcopy(self.inputs[key].signal)
          self.outputs[outkey].signal = ComplexSignal(self.inputs[key].signal)
          # The default name is not acceptable. This is a crude ad hoc fix!
          oldname = self.outputs[outkey].signal.name
          self.outputs[outkey].signal.name =oldname[:3]+band+oldname[3:]
          self.logger.debug(" _update_self: output port %s signal is %s",
                            outkey, self.outputs[outkey].signal)
          self.outputs[outkey].signal['frequency'] = int(band) # GHz
          self.outputs[outkey].signal['bandwidth'] = 2 # GHz
          #print "%s %s signal frequency is %s" % (self,
          #                                        self.outputs[outkey],
          #                            self.outputs[outkey].signal['frequency'])
      #show_signal(self, self.outputs)
         
  class PolSection(WBDC_core.PolSection):
    """
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      mylogger = logging.getLogger(module_logger.name+".PolSection")
      self.name = name
      WBDC_core.PolSection.__init__(self, parent, name, inputs=inputs,
                                  output_names=output_names,
                                  active=active)
      self.logger = mylogger
      self.logger.debug(" __init__: output names: %s",
                        output_names)
      self.logger.debug(" initializing WBDC2 %s", self)
      self.logger.info(" %s inputs: %s", self, str(self.inputs))
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
      self.logger.info(" %s outputs: %s", self, str(self.outputs))

    def set_pol_mode(self,circular=False):
      super(WBDC2.PolSection,self).set_pol_mode(circular)
      return self.get_pol_mode()

    def get_pol_mode(self):
      """
      """
      self.logger.debug("(WBDC2) get_pol_mode: invoked")
      mode = super(WBDC2.PolSection, self).get_pol_mode()
      return mode

  class DownConv(WBDC_core.DownConv):
    """
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):    
      mylogger = logging.getLogger(module_logger.name+".DownConv")
      self.name = name
      show_signal(self, inputs)
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

    def set_IF_mode(self, SB_separated=False):
      super(WBDC_core.DownConv, self).set_IF_mode(SB_separated=SB_separated)
      self.logger.debug(" IF mode set for SB separation is %s", SB_separated)
      self._update_self()
      return self.get_IF_mode()
