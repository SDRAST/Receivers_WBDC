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
      monitor_data = {}
      for latchgroup in [1,2]:
        MD = self.analog_monitor.get_monitor_data(latchgroup)
        for key in MD.keys():
          monitor_data[key] = MD[key]
      return monitor_data
    elif option == 41:
      # set crossover switch
      return self.crossSwitch.set_state(crossover=True)
    elif option == 42:
      # unset crossover switch
      return self.crossSwitch.set_state(crossover=False)
    elif option == 43:
      # set polarizer to circular
      states = {}
      for ps in self.pol_sec.keys():
        states[ps] = self.pol_sec[ps].set_state(True)
      return states
    elif option == 44:
      # set polarizers to linear
      states = {}
      for ps in self.pol_sec.keys():
        states[ps] = self.pol_sec[ps].set_state(False)
      return states
    elif option == 45:
      # set IQ hybrids to IQ
      states = {}
      for dc in self.DC.keys():
        states[dc] = self.DC[dc].set_state(True)
      return states
    elif option == 46:
      # set IQ hybrids to UL
      states = {}
      for dc in self.DC.keys():
        states[dc] = self.DC[dc].set_state(False)
      return states
    elif option == 47:
      # report the attenuator settings
      pass
    else:
      return ("invalid option %d" % option)
  
  def set_atten(self, ID, dB):
    """
    """
    pol_id = ID[:5]
    self.logger.debug("set_atten: pol section is %s", pol_id)
    self.pol_sec[pol_id].atten[ID].set_atten(dB)
  
  def get_atten(self, ID):
    pass
    
  
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
