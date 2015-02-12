"""
Module to provide class WBDC_core

Monitor and Control
===================

For a description of the generic Wide Band Down Converter see/do
MonitorControl.Receivers.WBDC.__doc__.split('\n')

Monitor and control is done with two or three LabJacks. For a detailed
description of the LabJack see/do
MonitorControl.Electronics.Interfaces.LabJack.__doc__.split('\n')

The LabJack with local ID 1 controls and reads switches, and reads analog
data (currents, voltages, temperatures). Details are described in
/home/kuiper/DSN/technical/Band K/Kband-downconv/Smith-Weinreb/\
WBDC{1|2}/DigitalBoard/ControlLogic.ods

LabJack 2 (and 3 for WBDC2) control attenuators using TickDACs to provide
analog control voltages.

LabJack 1
---------

This LabJack controls the WBDC motherboard.  The motherboard has groups of
8-bit latches which are used to control and sense switches.  A LatchGroup
class is provided by module latchgroup.py

Labjack 2 (and 3): Attenuators
------------------------------

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

LabJack 2 (and 3) Typical Configuration
---------------------------------------
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
import logging
import u3

import Math
import MonitorControl
from MonitorControl import ObservatoryError, show_port_sources
from MonitorControl.Receivers.WBDC import WBDC_base
from MonitorControl.Receivers.WBDC.latchgroup import LatchGroup
from Electronics.Interfaces.LabJack import connect_to_U3s, LJTickDAC

module_logger = logging.getLogger(__name__)

class WBDCerror(Exception):
  """
  """
  def __init__(self, format, *args):
    super(WBDCerror, self).__init__(*args)
    self.args = args
    self.message = format % args

  def __str__(self):
    return repr(self.message)

class WBDC_core(WBDC_base):
  """
  A class to provide the generic WBDC monitor and control functionality.

  It implements most of the methods originally in the {\tt WBDC_1} module as
  class methods. The addresses of the monitor and control points are likely to
  be different for the two WBDC implementations so these must be provided in
  dictionaries in the appropriate sub-classes.
  """
  def __init__(self, name, inputs = None, output_names=None, active=True):
    """
    Initialize a physical WBDC object.

    At least one Signal instance must be specified for inputs.

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
    self.logger = logging.getLogger(module_logger.name+".WBDC_core")
    self.logger.debug(" WBDC_core initializing %s", self)
    if inputs:
      self.logger.debug(" %s inputs: %s", self, str(self.inputs))
    LJ_keys = self.find_labjacks()
    if self.has_labjack(1):
      self.configure_MB_labjack()
    else:
      raise WBDCerror("could not configure motherboard Labjack")

  def find_labjacks(self):
    """
    Find the LabJacks for this WBDC

    WBDC1 has two LabJacks numbered 1 and 2.  WBDC has three LabJacks.
    LabJack 1 is the motherboard controller.  LabJacks 2 and 3 control the PIN
    diode attenuators.

    WBDC1 has a LabJack 3 which is the front-end controller.
    """
    self.logger.debug("find_labjacks: entered")
    self.LJ = connect_to_U3s()
    self.logger.info("find_labjacks: found %s", self.LJ.keys())
    return self.LJ.keys()

  def has_labjack(self, localID):
    """
    """
    if self.LJ.has_key(localID):
      return True
    else:
      self.logger.error(" %s has no LabJack %d", self.name, localID)
      return False

  def configure_MB_labjack(self):
    """
    Configure LabJack 1 for digital module control and analog monitoring
    """
    if self.has_labjack(1):
      # Analog input for voltages, currents and temperatures
      FIOanalog = int('00001111',2)
      self.LJ[1].configIO(FIOAnalog=FIOanalog,EIOAnalog=0)
      CIOBitDir = int('1111',2)
      EIOBitDir = int('11111111',2)
      FIOBitDir = int('00000000',2)
      direction = [FIOBitDir, EIOBitDir, CIOBitDir]
      mask = [0xff,0xff,0xff]
      self.logger.debug("LabJack %d direction=%s, write mask=%s",
                        self.LJ[1].localID, direction, mask)
      try:
        status = self.LJ[1].getFeedback(u3.PortDirWrite(Direction=direction,
                                                        WriteMask=mask))
        self.logger.debug(" configure status: %s", status)
      except Exception, details:
        self.logger.error(" Could not set bit direction on U3 %d",
                          self.LJ[1].localID)
        raise ObservatoryError("","configuring LJ 1 failed:\n"+str(details))
    else:
      raise ObservatoryError("","LabJack 1 is not connected")
    
  def configure_atten_labjack(self, ID):
    """
    Configure a LabJack for PIN diode attenuator control
    """
    if self.has_labjack(ID):
      self.LJ[ID].configIO(EIOAnalog=0, FIOAnalog=0)
      CIOBitDir = int('0000',2)
      EIOBitDir = int('00000000',2)
      FIOBitDir = int('00000000',2)
      direction = [FIOBitDir, EIOBitDir, CIOBitDir]
      mask = [0xff,0xff,0xff]
      self.logger.debug(" LabJack %d direction=%s, write mask=%s",
                        ID, direction, mask)
      try:
        status = self.LJ[ID].getFeedback(u3.PortDirWrite(Direction=direction,
                                                         WriteMask=mask))
        self.logger.debug(" configure status: %s", status)
      except Exception, details:
        self.logger.error(" Could not set bit direction on U3 %d",
                          self.LJ[ID].localID)
        raise ObservatoryError("LabJack "+str(ID),
                               "not configured:\n"+str(details))
    else:
      raise ObservatoryError("LabJack "+str(ID)," is not connected")

  class TransferSwitch(WBDC_base.TransferSwitch):
    """
    Beam to down-converter transfer switch

    There is one Switch object for each front-end polarization P1 and P2.

    At some point this might become a general transfer switch class
    """
    def __init__(self, parent, name, inputs=None, output_names=None):
      self.name = name
      mylogger = logging.getLogger(module_logger.name+".TransferSwitch")
      mylogger.debug(" initializing %s", self)
      mylogger.debug(" %s inputs: %s", self, str(inputs))
      WBDC_base.TransferSwitch.__init__(self, parent, name, inputs=inputs,
                                        output_names=output_names)
      self.logger = mylogger
      mylogger.debug(" %s inputs: %s", self, str(inputs))
      self.parent = parent

    class Xswitch(WBDC_base.TransferSwitch.Xswitch):
      """
      Monitor and control for WBDC transfer-switch

      This just initializes the superclass.  Sensing is the same for WBDC1 and
      WBDC2 but for control the other bits on their respective latch groups
      serve different function.  Hence , _set_state() must be defined in the
      subclass.
      """
      def __init__(self, parent, name, inputs=None, output_names=None,
                   active=True):
        self.name = name
        WBDC_base.TransferSwitch.Xswitch.__init__(self, parent, name,
                                                  inputs=inputs,
                                                  output_names=output_names,
                                                  active=active)
        
     
    #def get_crossover(self):
    #  """
    #  This gets the state from the hardware.
    #
    #  This method must be equated to the Switch object method _get_state()
    #
    #  The state of the switches is read at bits 0 and 1 of latch group 87.
    #  """
    #  subswitch = self.data[ID]
    #  self.logger.debug(" getting state for %s", subswitch)
    #  devID = subswitch.name
    #  rx = subswitch.parent.parent
    #  lg = LatchGroup(parent=rx, address=87)
    #  status = lg.read()
    #  self.logger.debug(" Latch Group 1 data = %s",
    #                    Math.decimal_to_binary(status,8))
    #  # This is a case of getting signal information from a name; bad!
    #  #test_bit = int(devID[-1])
    #  test_bit = WBDC_base.pol_names.index(ID)
    #  subswitch.state = status & test_bit
    #  self.logger.debug(" switch state = %d", subswitch.state)
    #  return subswitch.state

  class RFsection(WBDC_base.RFsection):
    """
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      self.parent = parent
      mylogger = logging.getLogger(module_logger.name+".RFsection")
      mylogger.debug(" initializing WBDC_core %s", self)
      show_port_sources(inputs,
                        "WBDC_core.RFsection inputs before superclass init:",
                        mylogger.level)
      WBDC_base.RFsection.__init__(self, parent, name, inputs=inputs,
                                  output_names=output_names, active=True)
      show_port_sources(self.inputs,
                        "WBDC_core.RFsection inputs after superclass init:",
                        mylogger.level)
      show_port_sources(self.outputs,
                        "WBDC_core.RFsection outputs after superclass init:",
                        mylogger.level)
      self.logger = mylogger

  class PolSection(WBDC_base.PolSection):
    """
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      mylogger = logging.getLogger(parent.logger.name+".PolSection")
      self.name = name
      self.parent = parent
      mylogger.debug(" initializing WBDC_core %s", self)
      WBDC_base.PolSection.__init__(self, parent, name, inputs=inputs,
                                  output_names=output_names,
                                  active=active)
      self.logger = mylogger
      self.logger.debug(" __init__: output names: %s",
                        output_names)
      self.logger.debug(" initialized WBDC_core %s", self)
      self.logger.debug(" %s inputs: %s", self, str(self.inputs))
      self.logger.debug(" %s outputs: %s", self, str(self.outputs))

    def get_mode(self):
      """
      """
      #self.logger.debug("WBDC_core.WBDC_core.get_pol_mode: invoked")
      self.mode = self._get_mode() # super(WBDC_core.PolSection,self).get_pol_mode()
      if self.convert:
        self.pols = ["L", "R"]
      else:
        self.pols = ["X", "Y"]
      return self.mode

    def _get_mode(self):
      """
      Report whether feed polarization is circular.

      Latches 2 and 3 (addresses 85 and 86) monitor the polarizer switches.
      Latch 2 is for receiver chain 1 (R1) and latch 3 for R2.
      For R1, bits 0-4 control the switches for bands 26-18, in that order.
      For R2, bits 0-4 control the switches for bands 18-26, in that order.
      For each, a value of 0 indicates linear and 1 indicates circular.

      @return: bool
      """
      if self.data.has_key('receiver') and self.data.has_key('band'):
        if self.data['receiver'] == 'R1':
          LG = self.parent.lg['R1PR'] # latchAddress = 85
          bitMask = 26-int(self.data['band'])
        elif self.data['receiver'] == 'R2':
          LG = self.parent.lg['R2PR'] # latchAddress = 86
          bitMask = int(self.data['band'])-18
        else:
          raise ObservatoryError(self.data['receiver'],
                                'is an invalid receiver chain')
      else:
        return None
      bits = LG.read() # LatchGroup(parent=self.parent, address=latchAddress).read()
      if bits == None:
        # There was a problem with the read
        return None
      self.logger.debug("  WBDC_core._get_mode: %s band %s latch bits: %s",
                        self, self.data['band'],
                        Math.decimal_to_binary(bits,8))
      maskedBit = bits & bitMask
      self.logger.debug("  WBDC_core._get_mode: masked bit: %s",
                        Math.decimal_to_binary(maskedBit,8))
      return bool(maskedBit)

  class DownConv(WBDC_base.DownConv):
    """
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      WBDC_base.DownConv.__init__(self, parent, name, inputs=inputs,
                                 output_names=output_names,
                                 active=active)
      self.logger = logging.getLogger(module_logger.name+".DownConv")


class OldAttenuator(LJTickDAC):
  """
  Voltage-controlled PIN diode attenuator for WBDC
  to be removed

  @type bias_list : list of float
  @ivar bias_list : bias voltages for calibration

  @type volts : list of float
  @ivar volts : auto-generated control voltages for calibration (V)

  @type pwrs : list of float
  @ivar pwrs : measured powers corresponding to 'volts' (dBm)

  @type bias : float
  @ivar bias : best bias value out of 'bias_list'

  @type coefs : numpy array of float
  @ivar coefs : polynomial coeffients for best calibration curve

  @type lower : float
  @ivar lower : lowest power measured

  @type upper : float
  @ivar upper : highest power measured

  @type atten_table : dictionary
  @ivar atten_table : control voltage indexed by attenuation
  """
  def __init__(self,LabJack,pin):
    """
    """
    LJTickDAC.__init__(self,LabJack,pin)
    print "Initializing attenuator on LabJack",LabJack.localID
    self.pwrs = {}
    self.bias = 3.0
    # The IDs match the WBDC receiver channels
    if pin == 0:
      self.ID = 1
      self.coefs = NP.array([2.24305829e-03,  3.47608278e-02,
                             1.91564653e-01,  3.57628078e-01,
                            -4.44852926e-01, -2.43563471e+00,
                            -4.14345128,     -8.16101008])
      self.lower = -5.0
      self.upper =  1.75
    elif pin == 2:
      self.ID = 2
      self.coefs = NP.array([1.97246882e-03,  3.15527700e-02,
                             1.80115477e-01,  3.54211343e-01,
                            -3.82845997e-01, -2.30612599,
                            -4.14205717,     -8.34552823    ])
      self.lower = -5.0
      self.upper =  1.75
    elif pin == 4:
      self.ID = 3
      self.coefs = NP.array([2.06521060e-03,  3.27308482e-02,
                             1.84436385e-01,  3.52212701e-01,
                            -4.20502519e-01,  -2.32719384,
                            -4.05112656,      -8.39222065   ])
      self.lower = -5.0
      self.upper =  1.75
    elif pin == 6:
      if LabJack.localID == 2:
        self.ID = 4
        self.coefs = NP.array([2.13996316e-03,  3.34458388e-02,
                               1.85709249e-01,  3.46131441e-01,
                              -4.43162863e-01, -2.31329518,
                              -3.91949192,     -8.55680332])
        self.lower = -5.0
        self.upper =  1.75
      elif LabJack.localID == 3:
        self.ID = 5
        self.coefs = NP.array([-1.11465757e-04, -9.83309141e-04,
                                1.73887763e-03,  2.92728140e-02,
                                3.68747270e-02, -4.86525897e-02,
                               -4.63506048e-01,  -2.74735018])
        self.lower = -6.0
        self.upper =  1.75
    else:
      self.ID = None
    self.volts = [self.lower,self.upper]

  def set_default(self):
    """
    This sets all attenuators to 5 dB, based on a previous
    calibration.
    """
    if self.ID == 1:
      self.setVoltages([3.0,-0.370])
    elif self.ID == 2:
      self.setVoltages([3.0,-0.539])
    elif self.ID == 3:
      self.setVoltages([3.0,-0.490])
    elif self.ID == 4:
      self.setVoltages([3.0,-0.724])
    elif self.ID == 5:
      self.setVoltages([3.0,-0.5])

  def get_calibration_data(self, pm,
                           limits=None,
                           bias=None,
                           save=True,
                           filename=None,
                           show_progress=False):
    """
    Obtains measured power as a function of control voltage

    This gets the data needed to calibrate a PIN diode attenuator
    between 'limits' ( = (lower,upper) ) control voltages.
    'bias' is an optional list of bias voltages.

    Generates these public attributes:
      - self.bias_list
      - self.volts
      - self.pwrs

    @type pm : Gpib.Gpib instance
    @param pm : power meter for the power readings

    @type limits : tuple of float
    @param limits : (lower test voltage, upper test voltage). If limits
    is not provided, (-5,1.75) will be used.

    @type bias : list of float
    @param bias : bias voltages for the PIN diode. ints are acceptable.
    If bias is not a list but a number it will be converted to a list.
    So far, the diodes tested have a best bias of 3.0 V.

    @type save : bool
    @param save : True to save data to a file

    @type filename : str
    @param filename : name of text file for data.  If it is not provided
    the data will not be saved.  If it is "", the file will be in the
    current directory with a default name

    @return: dictionary of control voltage lists, dictionary of measured
    powers, both indexed by bias voltage, and a list of biases.
    """
    pwrs = {}
    if bias == None:
      self.bias_list = [2, 2.5, 3, 3.5, 4]
    elif type(bias) == float or type(bias) == int:
      self.bias_list = [bias]
    else:
      self.bias_list = bias
    if limits == None:
      minV, maxV = -5, 1.75
    else:
      # arrange for 0.25 V steps
      minV = round(limits[0]*4)/4.
      maxV = round(limits[1]*4)/4.
    num_steps = int((maxV - minV)/.25)+1
    self.volts = NP.linspace(minV,maxV,num_steps)
    for bias in self.bias_list:
      if show_progress:
        print "Doing bias of",bias,"V",
      self.pwrs[bias] = []
      for volt in self.volts:
        self.setVoltages([bias,volt])
        if show_progress:
          print ".",
          sys.stdout.flush()
        # Give the power meter time to range and settle
        time.sleep(1)
        self.pwrs[bias].append(float(pm.read().strip()))
      if show_progress:
        print

    text = "# Attenuator "+str(self.ID)+"\n"
    text += "# Biases: "+str(self.bias_list)+"\n"
    for index in range(len(self.volts)):
      text += ("%5.2f " % self.volts[index])
      for bias in self.bias_list:
        text += ("  %7.3f" % self.pwrs[bias][index])+"\n"
    if filename != None:
      if filename:
        datafile = open(filename,"w")
      else:
        datafile = open("atten-"+str(self.ID)+".txt","w")
      datafile.write(text)
      datafile.close()
    return text

  def controlVoltage(self,pwr):
    """
    Compute control voltage for a given attenuation

    @return: float control voltage V
    """
    function = scipy.poly1d(self.coefs)
    minV = self.volts[0]
    maxV = self.volts[-1]
    return scipy.optimize.bisect(function-pwr,minV,maxV)

  def set_atten(self,atten):
    """
    Set the attenuation


    """
    if atten > 0.0:
      atten *= -1.
    if atten > 15:
      raise "Too much attenuation requested"
    else:
      volt = self.controlVoltage(atten)
      self.setVoltages([self.bias,volt])

  def useful_range(self,polycoefs):
    """
    Report minimum and maximum measurable attenuation.

    @type polycoefs : numpy array of float
    @param polycoefs : polynomial coefficients
    """
    function = scipy.poly1d(polycoefs)
    return Math.ceil(function(self.volts[-1])*10)/10, \
           Math.floor(function(self.volts[0])*10)/10

  def atten(self,polycoefs,controlV):
    """
    @type polycoefs : numpy array of float
    @param polycoefs : polynomial coefficients

    @type controlV : float
    @param controlV : control voltage (V)
    """
    return function - scipy.poly1d(polycoefs)(controlV)

  def fit_calibration_data(self):
    """
    Fit the power vs voltage curves taken with self.get_calibration_data().

    Generates these public attributes:
      - bias
      - coefs
      - lower
      - upper
      - atten_table
    """
    pwr_range = 0
    for bias in self.bias_list:
      polycoefs = scipy.polyfit(self.volts, self.pwrs[bias], 7)
      yfit = scipy.polyval(polycoefs,self.volts)
      lower,upper = self.useful_range(polycoefs)
      if (upper-lower) > pwr_range:
        pwr_range = upper-lower
        best_coefs = polycoefs
        self.coefs = scipy.polyfit(self.volts,
                                   NP.array(self.pwrs[bias])-upper,
                                   7)
        best_lower, best_upper = lower, upper
        self.bias = self.bias_list
    if pwr_range:
      # self.bias should now have the best bias (if there was more than
      # one to try, and a set of polynomial coefficients
      self.lower = best_lower
      self.upper = best_upper
      self.atten_table = {}
      for pwr in NP.arange(self.lower,self.upper,1):
        ctrlVolts = self.controlVoltage(pwr-self.upper)
        self.atten_table[self.upper-pwr] = ctrlVolts
      self.atten_table[0] = self.controlVoltage(0)
      return True
    else:
      return False
