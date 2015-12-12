"""
WBDC2 hardware monitor and control

Connecting to the Server
------------------------
Pyro clients can connect to it to request services. Here's an example of using
the server.  If the server is behind a firewall, it requires that an ssh tunnel
has been opened through the firewall to the pyro server host.  Function
'device_server' handles that transparently but you'll need a passcode
generator::
  kuiper@kuiper:~/Downloads$ ipython
  ...
  In [1]: from support.pyro import get_device_server, cleanup_tunnels
  In [2]: srvr = get_device_server('WBDC2hw_server-WBDC')

"""

import Pyro
from Pyro.errors import NamingError

import sys
import logging
import numpy

from MonitorControl import MCserver
from MonitorControl.Receivers.WBDC.WBDC2.WBDC2hwif import WBDC2hwif
from support.logs import set_module_loggers
from support.logs import init_logging, get_loglevel, set_loglevel
from support.pyro import launch_server
from support.process import is_running

module_logger = logging.getLogger(__name__)

class WBDC2hw_server(MCserver, WBDC2hwif):
  """
  """
  def __init__(self, name):
    """
    """
    self.logger = logging.getLogger(module_logger.name+".WBDC2hw_server")
    super(WBDC2hw_server,self).__init__()
    self.logger.debug(" superclass initialized")
    WBDC2hwif.__init__(self, name)
    self.logger.debug(" hardware interface instantiated")
    self.run = True

  def set_WBDC(self,option):
    """
    Emulate old WBDC1 server
    """
    if option == 38:
      # get analog data
      return self.get_monitor_data()
    elif option == 41:
      # set crossover switch
      return self.set_crossover(True)
    elif option == 42:
      # unset crossover switch
      return self.set_crossover(False)
    elif option == 43:
      # set polarizer to circular
      return self.set_polarizers(True)
    elif option == 44:
      # set polarizers to linear
      return self.set_polarizers(False)
    elif option == 45:
      # set IQ hybrids to IQ
      return self.sideband_separation(False)
    elif option == 46:
      # set IQ hybrids to UL
      return self.sideband_separation(True)
    elif option == 47:
      # report the attenuator settings
      report = {}
      for key in self.get_atten_IDs():
        report[key] = self.get_atten(key)
      return report
    else:
      return ("invalid option %d" % option)
  
  def get_atten_IDs(self):
    """
    Returns the names of all the attenuators
    """
    report = []
    for ps in self.pol_sec.keys():
      for att in self.pol_sec[ps].atten.keys():
        report.append(att)
    report.sort()
    return report
  
  def set_atten_volts(self, ID, V):
    """
    Sets the designated attenuator voltage
    """
    pol_id = ID[:5]
    self.logger.debug("set_atten: pol section is %s", pol_id)
    self.pol_sec[pol_id].atten[ID].VS.setVoltage(V)
    return True
  
  def get_atten_volts(self, ID):
    """
    Return attenuator voltage
    
    The voltage source remembers the last requested voltage.  If voltage has
    not been set, it is the default of 0 V.
    """
    pol_id = ID[:5]
    volts = self.pol_sec[pol_id].atten[ID].VS.volts
    if not volts:
      volts = 0.0
      self.pol_sec[pol_id].atten[ID].VS.volts = volts
    return volts
    
  def set_atten(self, ID, dB):
    """
    Sets pol section quad hybrid input attentuator
    
    @param ID : attenuator identifier
    @type  ID : str
    
    @param atten : requested attenuation
    @type  atten : float
    """
    pol_id = ID[:5]
    self.logger.debug("set_atten: pol section is %s", pol_id)
    self.pol_sec[pol_id].atten[ID].set_atten(dB)
    return self.pol_sec[pol_id].atten[ID].atten
  
  def get_atten(self, ID):
    """
    Returns the attenuation to which the specified attenuator is set.
    
    This does not query the hardware.  The attenuator simply remembers the last
    requested attenuation.  If 'set_atten' has not been used, it rteurns a
    blank.
    """
    pol_id = ID[:5]
    self.logger.debug("set_atten: pol section is %s", pol_id)
    return self.pol_sec[pol_id].atten[ID].get_atten()
  
  def get_monitor_data(self):
    """
    Returns the analog voltages, currents and temperatures
    """
    monitor_data = {}
    for latchgroup in [1,2]:
      MD = self.analog_monitor.get_monitor_data(latchgroup)
      for key in MD.keys():
        monitor_data[key] = MD[key]
    return monitor_data
  
  def set_crossover(self, crossover):
    """
    Set or unset the crossover switch
    """
    return self.crossSwitch.set_state(crossover)
  
  def get_crossover(self):
    """
    Set or unset the crossover switch
    """
    return self.crossSwitch.get_state()

  def set_polarizers(self, state):
    """
    Set all polarizers to the specified state
    
    True for E/H to L/R conversion.  Flase for bypass.
    """
    states = {}
    for ps in self.pol_sec.keys():
      states[ps] = self.pol_sec[ps].set_state(state)
    return states

  def get_polarizers(self):
    """
    Set all polarizers to the specified state
    
    True for E/H to L/R conversion.  Flase for bypass.
    """
    states = {}
    for ps in self.pol_sec.keys():
      states[ps] = self.pol_sec[ps].get_state()
    return states

  def sideband_separation(self, state):
    """
    Convert I/Q to LSB/USB
    
    When a hybrid state is 1 or True, the hybdrids are bypassed.  This is the
    default (on power up) state.  When the state is 0 or False, the hybrid is
    engaged to convert the complex IF (I and Q) to lower and upper sidebands.
    
    To make this function more intuitive, the logic is inverted here, that is,
    True means that the sidebands are separated.
    """
    states = {}
    for dc in self.DC.keys():
      states[dc] = self.DC[dc].set_state(1-int(state))
    return states
    
  def get_IF_hybrids(self):
    """
    Returns the state of the IQ-to-LU hybrids.
    
    True means that the hybrid is bypassed, False that it is engaged.
    """
    states = {}
    for dc in self.DC.keys():
      states[dc] = self.DC[dc].get_state()
    return states
          
if __name__ == "__main__":
  logpath = "/usr/local/logs/"
  nameserver_host = "crux"
  from socket import gethostname
  __name__ = 'wbdc2hw_server-'+gethostname()

  logging.basicConfig(level=logging.INFO)
  mylogger = logging.getLogger()
  mylogger = init_logging(mylogger,
               loglevel = logging.DEBUG,
               consolevel = logging.DEBUG,
               logname = logpath+__name__+".log")
  mylogger.debug(" Handlers: %s", mylogger.handlers)
  loggers = set_module_loggers(
    {'MonitorControl':                                'debug',
     'MonitorControl.Receivers.WBDC.WBDC2.WBDC2hwif': 'debug',
     'support':                                       'debug'})

  from optparse import OptionParser
  p = OptionParser()
  p.set_usage(__name__+' [options]')
  p.set_description(__doc__)

  p.add_option('-l', '--log_level',
               dest = 'loglevel',
               type = 'str',
               default = 'info',
               help = 'Logging level for main program and modules')
  opts, args = p.parse_args(sys.argv[1:])

  set_loglevel(mylogger, get_loglevel(opts.loglevel))

  # Set the module logger levels no lower than my level.
  for lgr in loggers.keys():
    if loggers[lgr].level < mylogger.level:
      loggers[lgr].setLevel(mylogger.level)
    mylogger.info("%s logger level is %s", lgr, loggers[lgr].level)


  # overrides pyro_support trace level
  Pyro.config.PYRO_TRACELEVEL = 3

  # Is there a Pyro server running?
  # if is_running("pyro-ns") == False:
  locator = Pyro.naming.NameServerLocator()
  mylogger.debug("Using locator %s", locator)
  # is this necessary?
  try:
    ns = locator.getNS(host=nameserver_host)
  except NamingError:
    mylogger.error(
      """Pyro nameserver task not found.
      If pyro-ns is not running. Do 'pyro-ns &'""")
    raise RuntimeError("No Pyro nameserver")
  # where is 'ns' used?
  mylogger.info("Starting %s, please wait....", __name__)
  # Here is the hardware configuration

  m = WBDC2hw_server("WBDC-2")
  mylogger.info("%s starting", __name__)
  launch_server(nameserver_host, __name__, m)
  mylogger.info("%s ending", __name__)
  try:
    ns = locator.getNS(host=nameserver_host)
  except NamingError:
    mylogger.error(
      """Pyro nameserver task notfound. Is the terminal at least 85 chars wide?
      If pyro-ns is not running. Do 'pyro-ns &'""")
    raise RuntimeError("No Pyro nameserver")
  try:
    ns.unregister(__name__)
  except NamingError:
    mylogger.debug("%s was already unregistered", __name__)
  mylogger.info("%s finished", __name__)
