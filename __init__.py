"""
WBDC - module for Wide Band Down Converter receiver classes

There are two versions of the widband down-converter.

WBDC1 has two RF sections after the band-splitting filters, one for 22 and
24 GHz, two switch-selectable LOs and one IF section.

WBDC2 has five RF sections and five IF sections.  The sections, as well as
feed switching, polarization selection, etc. are the same.

Input Switching
---------------
The first stage of the WBDC allows the down-converter groups to be switched
between the two feeds.

Polarization Conversion
-----------------------
After the band-selecting RF filters, the linearly polarized signals from each
feed can be switched into a quadrature hybrid to be converted to cicular
polarizations.

WBDC1 Band Selection
--------------------
There are two programmable local oscillators and a switch selects between
to define the band to be down-converted.

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
from support import contains, unique

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
  
  def __init__(self, name, inputs=None, output_names=None, active=True):
    """
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
  
class WBDC1(WBDC_base, Receiver):
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

    @param upstream : device providing the signals
    @type  upstream : Device instance

    @param name : unique identifier
    @type  name : str

    @param active : True is the FrontEnd instance is functional
    @type  active : bool

    @param inputs : a dict with sources for different inputs
    @type  inputs : dict of str:str
    """
    WBDC_base.__init__(self, name, active=active, inputs=inputs,
                      output_names=output_names)
    self.logger.debug("initializing %s", self)
    self.logger.info(" %s inputs: %s", self, str(self.inputs))
    
    self.band = self.set_band()
    self.data['bandwidth'] = 2e9 # Hz
    #self.DC = {}
    #dcs = WBDC_base.DC_names
    #dcs.sort()
    #for dc in dcs:
    #  dc_inputs = {}
      #for name in WBDC_base.pol_names:
        #dc_inputs[dc+name] = self.Xswitch[name].outputs[dc+name]
    #  for name in WBDC_base.pol_names:
    #    dc_inputs[dc+name] = self.rf_sec[name].outputs[dc+name]
    #  self.DC[dc] = self.DownConv(self, dc, inputs = dc_inputs)
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
        for IF in WBDC1.IF_names:
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
          index = WBDC1.IF_names.index(IFname)
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
