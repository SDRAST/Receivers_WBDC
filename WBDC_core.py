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
  
  def __init__(self, name, LJIDs, inputs = None, output_names=None, active=True):
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
    self.LJ = connect_to_U3s(LJIDs)
    self.lg = {'A1':    LatchGroup(parent=self, DM=0, LG=1),
               'A2':    LatchGroup(parent=self, DM=0, LG=2)}

  def report_analogs(self):
    all_data = {}
    for group in [1,2]:
      analog_data = self.analog_monitor.get_monitor_data(group)
      for key in analog_data.keys():
        all_data[key] = analog_data[key]
    return all_data

  def report_LJ_IO_config(self):
    report = {}
    for lj in self.LJ.keys():
      report[lj] = self.LJ[lj].configIO()
    return report

  def report_LJ_info(self):
    report = {}
    for lj in self.LJ.keys():
      report[lj] = self.LJ[lj].configU3()
    return report
      
      
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

  class DownConv(WBDC_base.DownConv):
    """
    """
    def __init__(self, parent, name, inputs=None, output_names=None,
                 active=True):
      WBDC_base.DownConv.__init__(self, parent, name, inputs=inputs,
                                 output_names=output_names,
                                 active=active)
      self.logger = logging.getLogger(module_logger.name+".DownConv")

  class AnalogMonitor(object):
    """
    """
    def __init__(self, parent, mon_points):
      """
      Initializes an analog data monitor
      
      @param mon_points : monitor point definitions (version specific)
      @type  mon_points : dict of dicts of lists of (int, str, str)
      """
      self.parent = parent
      self.mon_points = mon_points
      self.logger = logging.getLogger(self.parent.logger.name+".AnalogMonitor")

    def read_analogs(self, latchgroup=1):
      """
      """
      self.logger.debug("read_analogs: latch group=%d", latchgroup)
      latchAddress = latchgroup - 1
      self.logger.debug("read_analogs: latch address=%d", latchAddress)
      LGname = 'A'+str(latchgroup)
      self.logger.debug("read_analogs: latch name=%s", LGname)
      mon_data = self.mon_points[latchgroup]
      mon_pts = mon_data.keys()
      mon_pts.sort()
      self.logger.debug("read_analogs: monitor points: %s", mon_pts)
      analog_data = {}
      for point in mon_pts:
        mon_pt_addr = mon_data[point][0]
        self.logger.debug("read_analogs: sending %d", mon_pt_addr)
        self.parent.lg[LGname].write(mon_pt_addr)
        for dataset in [0,1]:
          self.logger.debug('read_analogs: dataset=%d',dataset)
          label =  mon_data[point][dataset+1].strip()
          self.logger.debug('read_analogs: reading %s', label)
          AINnum = latchAddress*2+dataset
          # in the next line, LGname can be A1 or A2
          self.logger.debug("read_analogs: reading AIN%d", AINnum)
          analog_data[label] = self.parent.lg[LGname].LJ.getAIN(AINnum)
          self.logger.debug("read_analogs: read %f", analog_data[label])
      return analog_data

    def get_monitor_data(self, latchgroup=1):
      """
      """
      monitor_data = {}
      analog_data = self.read_analogs(latchgroup)
      for ID in analog_data.keys():
        if ID:
          monitor_data[ID] = self.convert_analog(ID, analog_data[ID])
      return monitor_data
      
    def convert_analog(self, ID, value):
      """
      The subclass must replace this.
      """
      pass
 
  # ------------------------------- WBDC_core methods -------------------------

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
    

