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

WARNING!  RFsection method _rename_beam is very dependent on the naming
convention used, specifically, the length of the names.
"""
import logging
import copy
from collections import OrderedDict

from MonitorControl import Device, Switch, Port, IF,  ObservatoryError
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
    <--K_4ch--> <-----------------WBDC2------------------>
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
  pol_names  = ["P1", "P2"]
  RF_names   = ["R1", "R2"]
  out_pols   = ["PA", "PB"]
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
    Receiver.__init__(self, name, active=active, inputs=inputs,
                      output_names=output_names)
    self.logger = logging.getLogger(module_logger.name+".WBDC_base")
    self.logger.debug(" initializing for %s", self.name)
    self._create_pol_list(inputs)

    # In the next code block we:
    # 1) create two RF sections for each pol, one for each beam
    # 2) create two pols sections for each RF section, one per beam
    rfs = WBDC_base.RF_names
    rfs.sort()
    #self.rf_sec = {}
    #self.pol_sec = {}
    for rf in rfs:
      # This part creates the RF sections
      index = rfs.index(rf)
      rf_inputs = {}
      #outnames = []
      #for name in WBDC_base.pol_names:
      #  pindex = WBDC_base.pol_names.index(name)
      #  rf_inputs[rf+name] = self.Xswitch[name].outputs[rf+name]
      #  if self.band_names:
      #    for band in self.band_names:
      #      outnames.append(rf+band+name)
      #  else:
      #    outnames.append(rf+name)
      #self.logger.debug("WBDC_base.__init__: RF inputs is now %s", rf_inputs)
      #self.rf_sec[rf] = self.RFsection(self, rf, inputs = rf_inputs,
      #                                 output_names=outnames)
      #self.logger.debug("WBDC_base.__init__: RF outputs is now %s",
      #                  self.rf_sec[rf].outputs)
      # This part creates the pol sections
      #pol_inputs = OrderedDict(sorted(self.rf_sec[rf].outputs.items()))
      #self.logger.debug("WBDC_base.__init__: pol inputs is now %s",
      #                    pol_inputs)
      #for band in band_names:
      #    psec_inputs = {}
      #    for pol in WBDC_base.pol_names:
      #      psec_inputs[rf+band+pol] = pol_inputs[rf+band+pol]
      #    self.pol_sec[rf+band] = self.PolSection(self, rf+band,
      #                                            inputs = psec_inputs)
      #else:
      #  self.pol_sec[rf] = self.PolSection(self, rf, inputs = rf_inputs)
      #  band = ""
    #  self.logger.debug("WBDC_base.__init__: pol section %s outputs: %s",
    #          self.pol_sec[rf+band].name, self.pol_sec[rf+band].outputs.keys())
    #pol_sec_names = self.pol_sec.keys()
    #self.logger.debug("WBDC_base.__init__: pol sections: %s", pol_sec_names)

    # create mixer/IF (down-converter) sections
    #self.DC = {}
    #for name in pol_sec_names:
    #  for pol in WBDC_base.out_pols:
    #    self.logger.debug(" making DCs for %s", name+pol)
    #    self.logger.debug(" creating inputs for %s", name+pol)
    #    dc_inputs = {name+pol: self.pol_sec[name].outputs[name+pol]}
    #    self.DC[name+pol] = self.DownConv(self, name+pol,
    #                                      inputs = dc_inputs)
    #    self.DC[name+pol].set_IF_mode() # default is IQ
    #    self.logger.debug(" DC %s created", self.DC[name+pol])
    # report outputs
    #self.logger.info(" %s outputs: %s",
    #                 self, str(self.outputs))
    #self._update_self()
    #self.logger.debug(" initialized for %s", self.name)
    
  def _create_pol_list(self,inputs):
    """
    Create sorted lists of input, beam, and polarization names
    """
    self.inkeys = inputs.keys()
    self.inkeys.sort()
    self.pols = []
    for key in self.inkeys:
      self.pols.append(inputs[key].signal['pol'])
    self.pols = unique(self.pols)
    self.pols.sort()

  def set_crossover(self, crossed=False):
    """
    Set or unset the cross-over switch
    """
    self.Xswitch.set_crossover(crossed=crossed)
    self.Xswitch._update_self()
    return self.Xswitch.get_crossover()

  def _update_self(self):
    # update the transfer switch
    self.logger.debug(" updating %s", self)
    self.Xswitch._update_self()
    # update the RF sections:
    try:
      for key in self.rf_sec.keys():
        self.rf_sec[key]._update_self()
    except Exception, details:
      raise Exception, "Could not update RF section; "+str(details)
    try:
      for key in self.pol_sec.keys():
        self.pol_sec[key]._update_self()
    except Exception, details:
      raise Exception, "Could not update pol section; "+str(details)
    for key in self.DC.keys():
      self.DC[key]._update_self()

  class TransferSwitch(Device):
    """
    Beam to down-converter transfer switch

    There is one Switch object for each front-end polarization P1 and P2. Each
    switch is associated with 'data', which is defined in the Device super-
    class and allows the sub-switches to be accessed by providing the
    TransferSwitch instance with an index, 1 or 2.

    At some point this might become a general transfer switch class
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      mylogger = logging.getLogger(module_logger.name+".TransferSwitch")
      mylogger.debug(" initializing %s", self)
      mylogger.debug(" %s inputs: %s", self, str(inputs))
      self.name = name
      Device.__init__(self, name, inputs=inputs,
                      output_names=output_names, active=active)
      self.logger = mylogger
      self.logger.debug(" %s inputs: %s", self, str(self.inputs))
      self.parent = parent
      self.states = {}
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
      """
      This makes path changes consistent with the switch state
      """
      keys = self.data.keys()
      keys.sort()
      for sw in keys:
        self.data[sw].set_state(int(crossed))
        for name in self.outputs.keys():
          for prop in self.outputs[name].source.signal.keys():
            for destination in self.outputs[name].destinations:
              destination.signal[prop] = self.outputs[name].signal[prop]
      self._update_self()
      return self.get_crossover()

    def get_crossover(self):
      """
      """
      keys = self.data.keys()
      keys.sort()
      for ID in keys:
        self.states[ID] = self.data[ID].get_state()
      if self.states[keys[0]] == self.states[keys[1]]:
        self.state = self.states[keys[0]]
      else:
        raise ObservatoryError(str(self),
                       ("%s sub-switch states do not match"))
      return self.state

    def _update_self(self):
      for key in self.data.keys():
        self.data[key]._update_self()
                                     
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
      Receiver.RFsection.__init__(self, parent, name, inputs=inputs,
                                  output_names=output_names, active=True)
      self.logger = logging.getLogger(module_logger.name+".RFsection")
      self.logger.debug(" initializing WBDC_base %s", self)
      self.logger.info(" %s inputs: %s", self, str(self.inputs))
      self.logger.info(" %s outputs: %s", self, str(self.outputs))
      self._update_self()

    def _rename_beam(self,key):
      """
      This is a very ad-hoc way to replace BxPy with DxPz

      z is a capital letter designator corresponding to integer y.

      WARNING!  RFsection method _rename_beam is very dependent on the naming
      convention used, specifically, the length of the names.
      """
      key = "D"+key[1:]
      key = key[:3]+chr(64+int(key[3]))
      return key
     
    def _propagate(self):
      """
      Propagate signals from inputs to outputs
      """
      rx = self.name[:4]
      for pol in WBDC_base.pol_names:
        self.inputs[rx+pol].destinations = []
      for key in self.outputs.keys():
        for pol in WBDC_base.pol_names:
          if key[:2] == rx and key[-2:] == pol:
            self.outputs[key].source = self.inputs[rx+pol]
            self.inputs[rx+pol].destinations.append(self.outputs[key])

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
        #for band in WBDC2.bands:
        #  outkey = key[:2]+band+key[2:]
        #  self.outputs[outkey].signal = copy.copy(self.inputs[key].signal)
        #  self.logger.debug(" _update_self: output port %s signal is %s",
        #                    outkey, self.outputs[outkey].signal)
        #  self.outputs[outkey].signal['frequency'] = int(band) # GHz
        #  self.outputs[outkey].signal['bandwidth'] = 2 # GHz
        #else:
          # It's not clear how this can best handle WBDC1.  The state of
          # the LO switch must be factored in somehow.
          #self.outputs[key].signal = copy.copy(self.inputs[key].signal)
          #self.logger.debug(
          #               " _update_self: port signal is %s",
          #               self.outputs[newkey].signal)
          #self.outputs[key].signal['frequency'] = 22 # GHz
          #self.outputs[key].signal['bandwidth'] = 2 # GHz

  class PolSection(Receiver.PolSection):
    """
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      """
      """
      # create the output names
      mylogger = logging.getLogger(module_logger.name+".PolSection")
      self.output_names = []
      for pname in WBDC_base.out_pols:
        self.output_names.append(name+pname)
      self.output_names.sort()
      # initialize the superclass
      Receiver.PolSection.__init__(self, parent, name, inputs=inputs,
                                  output_names=self.output_names,
                                  active=active)
      self.logger = mylogger
      self.logger.debug(" __init__: output names: %s",
                        self.output_names)
      self.logger.debug(" initializing WBDC_base %s", self)
      self.logger.info(" %s inputs: %s", self, str(self.inputs))
      self.set_pol_mode() # defaults to X,Y
      self.logger.info(" %s outputs: %s", self, str(self.outputs))
      
    def set_pol_mode(self,circular=False):
      self.logger.debug(" set_pol_mode: invoked")
      self.circular = circular
      if self.circular:
        self.pols = ["L", "R"]
      else:
        self.pols = ["X", "Y"]
      self.get_pol_mode()

    def get_pol_mode(self):
      self.logger.debug("(base) get_pol_mode: invoked")
      self.circular = self._get_pol_mode()
      return self.circular

    def _get_pol_mode(self):
      self.logger.debug("(base) _get_pol_mode: invoked")
      return None
      
    def _propagate(self):
      """
      Propagate signals from inputs to outputs.

      The output port names are of the form RxFFPy where x is 1 or 2, FF is a
      two digit frequency code, and y is A or B.  The input names are similar
      except that y is 1 or 2.  This reflects the fact that the input
      polarizations are X and Y but the outputs may be those or R and L. The
      code below constructs the output names from the input names.
      """
      keys = self.outputs.keys()
      keys.sort()
      for key in keys:
        self.logger.debug("_propagate signal for output %s", key)
        self.outputs[key].source = []
        pol = key[-2:]
        self.logger.debug("_propagate: for pol %s", pol)
        pindex = WBDC_base.out_pols.index(pol) # 0 or 1
        self.logger.debug("_propagate: pol index = %d", pindex)
        name = key[:4]+WBDC_base.pol_names[pindex] # RxFFP1 or RxFFP2
        self.logger.debug("_propagate: new name is %s", name)
        if self.circular:
          self.outputs[key].source.append(self.inputs[name])
          self.inputs[name].destinations.append(self.outputs[key])
        else:
          self.logger.debug("_propagate: changing %s to %s",
                              self.outputs[key].source, self.inputs[name])
          self.outputs[key].source = self.inputs[name]
          self.inputs[name].destinations = [self.outputs[key]]
        self.logger.debug("_propagate: %s destinations: %s",
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
        pol_index = int(key[-1])-1
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

    def set_IF_mode(self, SB_separated=False):
      self.SB_separated = SB_separated
      if self.SB_separated:
        self.IF_mode = ["L","U"]
        self.data['bandwidth'] = 1e9
      else:
        self.IF_mode = ["I","Q"]
        self.data['bandwidth'] = 2e9
      return self.get_IF_mode()

    def get_IF_mode(self):
      return self.IF_mode

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
