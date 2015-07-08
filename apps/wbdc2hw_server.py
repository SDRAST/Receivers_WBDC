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
  def __init__(self, name):
    self.logger = logging.getLogger(module_logger.name+".WBDC2hw_server")
    super(WBDC2hw_server,self).__init__()
    self.logger.debug(" superclass initialized")
    WBDC2hwif.__init__(self, name)
    self.logger.debug(" hardware interface instantiated")
    self.run = True

logpath = "/tmp/" # for now
nameserver_host = "crux"

logging.basicConfig(level=logging.INFO)
mylogger = logging.getLogger()
init_logging(mylogger,
             loglevel = logging.INFO,
             consolevel = logging.DEBUG,
             logname = logpath+"WBDC2_server.log")
mylogger.debug(" Handlers: %s", mylogger.handlers)

if __name__ == "__main__":
  from socket import gethostname
  __name__ = 'wbdc2hw_server-'+gethostname()

  loggers = set_module_loggers(
    {'MonitorControl':                                'debug',
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
