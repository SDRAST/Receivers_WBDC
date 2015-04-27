"""
WBDC - module for Wide Band Down Converter receiver classes

Overview
========
There are two versions of the wideband down-converter

WBDC1 has two RF sections after the band-splitting filters, one for 22 and 24
GHz, two switch-selectable LOs and one IF section.

WBDC2 has five RF sections and five IF sections.

The sections, as well as feed switching, polarization selection, etc. are
basically the same.

Input Switching
===============
The first stage of the WBDC allows the down-converter groups to be switched
between the two feeds.

Polarization Conversion
=======================
After the band-selecting RF filters, the linearly polarized signals from each
feed can be switched into a quadrature hybrid to be converted to cicular
polarizations.

Sideband Separation
===================
The down-conversion produces complex outputs (i.e. a pair of signals I and
Q).  There are switches which can direct each I/Q pair into a quadrature
hybrid to convert them to an upper and lower sideband pair.

WARNING!  RFsection method _rename_beam is very dependent on the naming
convention used, specifically, the length of the names.
"""
import logging
import copy
from collections import OrderedDict

from MonitorControl import Device, Switch, Port, IF,  ObservatoryError
from MonitorControl import show_port_sources
from MonitorControl.Receivers import Receiver
from support import unique

module_logger = logging.getLogger(__name__)

class WBDC_base(Receiver):
  """
  Base class for a DSN K-band wideband down-converter::
          ---      ---        ---                ---
          | |--P1--| |--D1P1--| |== 5 sub-bands==| |==D1PA
          | |      | |        ---                | |
   >--B1--| |      | |                           | |
          | |      | |        ---                | |
          | |--P2--| |--D1P2--| |== 5 sub-bands==| |==D1PB
          ---      | |        ---                ---
                   | |   
          ---      | |        ---                ---
          | |--P1--| |--D2P1--| |== 5 sub-bands==| |==D2PA
          | |      | |        ---                | |
   >--B2--| |      | |                           | |
          | |      | |        ---                | |
          | |--P2--| |--D2P2--| |== 5 sub-bands==| |==D2PB
          ---      ---        ---                ---
          OMT     Xswitch  RFsection       pol_section X 5
   <---K_4ch-->  <-----------------WBDC2----------------->
    
  The DSN K-band WBDC systems have two dual polarization feeds. The feeds can
  be interchanged with a pair of transfer switches. 

  The signals from each feed and pol enter an RF section which splits the full
  band into five RF sub-bands and also measures the power coming in to the
  RF section.

  The five outputs from each of the RF section for each pol are passed into a
  polarization section.

  Class variables are used to name the sections of the WBDC.

  WARNING!  RFsection method _rename_beam is very dependent on the naming
  convention used, specifically, the length of the names.
  """
  pol_names  = ["E",  "H" ]
  RF_names   = ["R1", "R2"]
  out_pols   = ["P1", "P2"]
  DC_names   = ["D1", "D2"]
  IF_names   = ["I1", "I2"]
  
  def __init__(self, name, inputs=None, output_names=None,active=True):
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
    mylogger = logging.getLogger(module_logger.name+".WBDC_base")
    Receiver.__init__(self, name, active=active, inputs=inputs,
                      output_names=output_names)
    self.logger = mylogger
    self.logger.debug(" initializing for %s", self.name)
    self._create_pol_list(inputs)

    # The first element in a WBDC is the two-polarization feed transfer switch
    self.crossSwitch = self.TransferSwitch(self, "WBDC transfer switch",
                                       inputs=inputs)
        
  def _create_pol_list(self,inputs):
    """
    Create sorted lists of input, beam, and polarization names
    """
    if inputs:
      self.inkeys = inputs.keys()
      self.inkeys.sort()
      self.pols = []
      for key in self.inkeys:
        self.pols.append(inputs[key].signal['pol'])
      self.pols = unique(self.pols)
      self.pols.sort()

  def get_crossover(self):
    """
    Get the cross-over switch state
    """
    self.crossSwitch.get_state()
    #self.crossSwitch._update_self()
    return self.crossSwitch.state
    
  def set_crossover(self, crossover=False):
    """
    Set or unset the cross-over switch
    """
    self.crossSwitch.set_state(crossover=crossover)
    self.crossSwitch._update_self()
    return self.get_crossover()

  def _update_self(self):
    # update the transfer switch
    self.logger.debug("_update_self: updating %s", self)
    self.crossSwitch._update_self()
    # update the RF sections:
    try:
      for key in self.rf_section.keys():
        self.rf_section[key]._update_self()
    except Exception, details:
      raise Exception, "Could not update RF section; "+str(details)
    # update the pol sections:
    #try:
    for key in self.pol_sec.keys():
      self.pol_sec[key]._update_self()
    #except Exception, details:
    #  raise Exception, "Could not update pol section; "+str(details)
    for key in self.DC.keys():
      self.DC[key]._update_self()

  class TransferSwitch(Device):
    """
    Beam to down-converter transfer switch

    There is one Switch object for each front-end polarization X and Y. Each
    switch is associated with 'data', which is defined in the Device super-
    class and allows the sub-switches to be accessed by providing the
    TransferSwitch instance with an index, 1 or 2.

    With the switch unset, F1 -> R1, F2 -> R2.
    With the switch set, F1 -> R2, F2 -> R1

    There is no transfer switch defined for Receiver so this is the highest
    superclass for TransferSwitch.
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      mylogger = logging.getLogger(parent.logger.name+".TransferSwitch")
      self.name = name
      mylogger.debug(" initializing %s", self)
      mylogger.debug("__init__: initial %s inputs: %s", self, str(inputs))
      mylogger.debug(" output names: %s", output_names)
      Device.__init__(self, name, inputs=inputs,
                      output_names=output_names, active=active)
      self.logger = mylogger
      self.logger.debug(" %s inputs: %s", self, str(self.inputs))
      self.parent = parent
      self.states = {}
      # This directs the polarizations to the down-converters according
      # to ordered lists defined in WBDC_base
      self.logger.debug("__init__: parent pols: %s", parent.pols)
      for pol in parent.pols:
        pol_inputs = {}
        for key in parent.inkeys:
          if parent.inputs[key].signal['pol'] == pol:
            pol_inputs[key] = inputs[key]
        self.data[pol] = self.Xswitch(self, pol,
                                      inputs = pol_inputs,
                                      output_names = [WBDC_base.RF_names[0]+pol,
                                                      WBDC_base.RF_names[1]+pol])
      self.logger.debug("__init__: %s outputs: %s", self, str(self.outputs))

    def get_state(self):
      """
      Gets the TransferSwitch state from the Xswitch states.
      """
      keys = self.data.keys()
      keys.sort()
      for ID in keys:
        self.states[ID] = self.data[ID].get_state()
      if self.states[keys[0]] != self.states[keys[1]]:
        #raise ObservatoryError(str(self),
        #                  "%s sub-switch states do not match")
        self.logger.error("%s sub-switch states do not match",str(self))
      self.state = self.states[keys[0]]
      #self._update_self()
      self.logger.debug("WBDC_base.TransferSwitch.get_state: %s state is %s",
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
      self.logger.debug("WBDC_base.TransferSwitch.set_state: %s state is %s",
                        self, self.state)
      return self.state
     
    def _update_self(self):
      """
      Update the sub-switches

      Should not be needed
      """
      for key in self.data.keys():
        self.data[key]._update_signal()

    class Xswitch(Switch):
      """
      Single 2x2 switch in the dual-beam transfer switch.
      """
      def __init__(self, parent, name, inputs=None, output_names=None,
                   active=True):
        """
        Initializes one Switch superclass
        """
        mylogger = logging.getLogger(parent.logger.name+".Xswitch")
        self.parent = parent
        self.name = name
        mylogger.debug(" initializing %s", self)
        Switch.__init__(self, name, inputs, output_names, stype="2x2")
        self.logger = mylogger
        self.logger.debug(" initialized %s", self)
        self.get_state()

      def get_state(self):
        """
        Stub could be replaced by more elaborate sub-class version
        """
        #self.state = self._get_state()
        self.state = super(WBDC_base.TransferSwitch.Xswitch, self).get_state()
        #self._update_signal()
        self.logger.debug(
               "WBDC_base.TransferSwitch.Xswitch.get_state: %s signal updated",
               self)
        return self.state

      def _get_state(self):
        """
        Subclass must provide actual method for getting state, replacing this.
        """
        return self.state

      def set_state(self, state):
        """
        This makes path changes consistent with the switch state.  If a
        subclass defines a set_state method, then it should call this in turn
        to be sure that the inputs and outputs are redefined as needed.
        """
        # This actually sets the hardware switch, if defined by a subclass
        self._set_state(state)
        self.logger.debug(
                  "WBDC_base.TransferSwitch.Xswitch.set_state: %s state is %s",
                  self)
        # This redefines input destinations and output sources
        super(WBDC_base.TransferSwitch.Xswitch,self).set_state(state)
        self._update_signal()
        return self.get_state()
        
      def _set_state(self, state):
        """
        Subclass must provide actual method for getting state, replacing this.
        """
        self.state = state
        return self.state
        
  class RFsection(Receiver.RFsection):
    """
    An RF section may split the signal into several sub-bands.
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      """
      The default RF section just passes the signals through
      """
      self.parent = parent
      self.name = name
      mylogger = logging.getLogger(module_logger.name+".RFsection")
      mylogger.debug(" initializing WBDC_base %s", self)
      show_port_sources(inputs,
                        "WBDC_base.RFsection inputs before superclass init:",
                        mylogger.level)
      Receiver.RFsection.__init__(self, parent, name, inputs=inputs,
                                  output_names=output_names, active=True)
      show_port_sources(self.inputs,
                        "WBDC_base.RFsection inputs after superclass init:",
                        mylogger.level)
      show_port_sources(self.outputs,
                        "WBDC_base.RFsection outputs after superclass init:",
                        mylogger.level)
      self.logger = mylogger
      self._update_self()

  class PolSection(Receiver.PolSection):
    """
    Class for optionally converting E,H polarization to R,L polarization.
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      """
      The arguments are the same as for RFsection.
      """
      # create the output names
      mylogger = logging.getLogger(parent.logger.name+".PolSection")
      self.name = name
      mylogger.debug(" initializing base %s", self)
      mylogger.debug("__init__: inputs:%s", inputs)
      # creating output names; input should be None
      self.output_names = []
      for pname in WBDC_base.out_pols:
        self.output_names.append(name+pname)
      self.output_names.sort()
      mylogger.debug(" new output names: %s", self.output_names)
      # initialize the superclass
      Receiver.PolSection.__init__(self, parent, name, inputs=inputs,
                                  output_names=self.output_names,
                                  active=active)
      self.logger = mylogger
      self.logger.debug(" __init__: output names: %s",
                        self.output_names)
      self.logger.debug(" initializing WBDC_base %s", self)
      self.logger.debug(" %s inputs: %s", self, str(self.inputs))
      self.set_state() # defaults to E,H
      self.logger.debug(" %s outputs: %s", self, str(self.outputs))
      
    def set_state(self, convert=False):
      """
      This MUST get replaced by the appropriate sub-class method

      For software-only testing it is kept here.
      """
      self.logger.warning(" set pol mode invoked from superclass")
      self._set_state(convert)
      if self.state:
        self.pols = ["L", "R"]
      else:
        self.pols = ["E", "H"]

    def get_state(self):
      """
      This gets replaced by the sub-class
      """
      self.logger.debug("WBDC_base.get_state: invoked")
      self.state = self._get_state()
      return self.state

    def _set_state(self, state):
      """
      This gets replaced by the sub-class
      """
      self.state = state
      
    def _get_state(self):
      """
      This gets replaced by the sub-class
      """
      self.logger.debug("WBDC_base._get_state: invoked")
      return self.state

    def _propagate(self):
      """
      Propagate signals from inputs to outputs.

      The output port names are of the form RxFFPy where x is 1 or 2, FF is a
      two digit frequency code, and y is 1 or 2.  The input names are E and H
      or R and L, obtained from the prior RF sections. The code below
      constructs the output names from the input names.
      """
      keys = self.outputs.keys()
      keys.sort()
      for key in keys:
        self.logger.debug("WBDC._propagate: processing output %s", key)
        pol = key[-2:]
        polsecname = key[:-2]
        self.logger.debug("WBDC._propagate: for polsec %s, pol %s", polsecname, pol)
        # Figure out the corresponding input name
        pindex = WBDC_base.out_pols.index(pol) # 0 or 1
        self.logger.debug("WBDC._propagate: pol index = %d", pindex)
        # The following must be done this way because in another case the input
        # pols any be L and R.
        name = WBDC_base.pol_names[pindex] # E|L or H|R
        self.logger.debug("WBDC._propagate: input name is %s", name)
        self.outputs[key].source = []
        if self.state:
          self.outputs[key].source.append(self.inputs[name])
          self.inputs[name].destinations.append(self.outputs[key])
        else:
          self.logger.debug("WBDC._propagate: changing output %s from %s to %s",
                            self, self.outputs[key].source, self.inputs[name])
          self.outputs[key].source = self.inputs[name]
          self.inputs[name].destinations = [self.outputs[key]]
        self.logger.debug("WBDC._propagate: %s destinations: %s",
                            self.inputs[name], self.inputs[name].destinations)

    def _update_self(self):
      """
      """
      input_keys = self.inputs.keys()
      input_keys.sort()
      self.logger.debug(" _update_self: entered for %s",
                        self.name)
      self.logger.debug(" _update_self: pols: %s",
                        self.pols)
      self._propagate()
      for key in input_keys:
        self.logger.debug(
                   " _update_self: updating input %s", key)
        self.inputs[key].signal.copy(self.inputs[key].source.signal)
        self.logger.debug(" _update_self: signal is %s",
                          self.inputs[key].signal)
        index = input_keys.index(key)
        outkey = self.output_names[index]
        self.logger.debug(
             " _update_self: copying signal to %s", outkey)
        self.outputs[outkey].signal.copy(self.inputs[key].signal)
        pol_index = WBDC_base.pol_names.index(key)
        self.outputs[outkey].signal['pol'] = self.pols[pol_index]

  class DownConv(Receiver.DownConv):
    """
    ACTION: port relevant stuff from WBDC2
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      mylogger = logging.getLogger(module_logger.name+".DownConv")
      self.name = name
      mylogger.debug(" initializing %s", str(self))
      output_names = []
      for IF in WBDC_base.IF_names:
        ID = name+IF
        output_names.append(ID)
      mylogger.debug("DC %s outputs are %s", name, output_names)
      Receiver.DownConv.__init__(self, parent, name, inputs=inputs,
                                 output_names=output_names,
                                 active=active)
      self.logger = mylogger
      self._propagate()
      for nm in output_names:
        parent.outputs[nm] = self.outputs[nm]
      self.logger.debug(" %s outputs: %s", str(self), str(self.outputs))

    def set_state(self, SB_separated=False):
      self._set_state(SB_separated)

      if self.state:
        self.IF_mode = ["L","U"]
        self.data['bandwidth'] = 1e9
      else:
        self.IF_mode = ["I","Q"]
        self.data['bandwidth'] = 2e9
      return self.get_state()

    def _set_state(self, state):
      self.state = state
      
    def get_state(self):
      return self._get_state()

    def _get_state(self):
      return self.state
      
    def _propagate(self):
      """
      Propagate signals from inputs to outputs

      Input names are of the form RxFFPy, same as the names of the pol section
      outputs.  Output names have I1 or I2 appended.
      """
      for key in self.inputs.keys():
        for IF in WBDC_base.IF_names: # I1 or I2
          self.outputs[key+IF].source = self.inputs[key]
          self.inputs[key].destinations.append(self.outputs[key+IF])
        
    def _update_self(self):
      """
      """
      self.logger.debug(" _update_self: Updating %s outputs",
                        self)
      self._propagate()
      input_keys = self.inputs.keys()
      input_keys.sort()
      for key in input_keys:
        self.inputs[key].signal.copy(self.inputs[key].source.signal)
        for IF in WBDC_base.IF_names:
          index = WBDC_base.IF_names.index(IF)
          self.outputs[key+IF].signal.copy(self.inputs[key].signal)
          self.outputs[key+IF].signal.name = \
                    self.outputs[key+IF].source.signal.name+self.IF_mode[index]
          self.outputs[key+IF].signal['IF'] = self.IF_mode[index]
