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

from MonitorControl.Receivers.WBDC.WBDC2.WBDC2hwif import WBDC2hwif
from support.logs import set_module_loggers
from support.logs import init_logging, get_loglevel, set_loglevel
from support.pyro import launch_server
from support.process import is_running

module_logger = logging.getLogger(__name__)

class MCserver(Pyro.core.ObjBase):
  def __init__(self):
    Pyro.core.ObjBase.__init__(self)
    self.logger = logging.getLogger(module_logger.name+".MCserver")
    self.logger.debug("__init__: logger is %s",self.logger.name)
    self.run = True

  def sanitize(self, list_or_dict):
    """
    Pyro cannot return objects whose class is not known by the client.

    Any standard types of objects are returned as is.  A list or a dict,
    however, needs to be examined item by item to see if they are
    standard types.  Those that aren't need to be replaced with a string
    representation.
    """
    if type(list_or_dict) == str or \
       type(list_or_dict) == int or \
       type(list_or_dict) == float or \
       type(list_or_dict) == bool:
      return list_or_dict
    elif type(list_or_dict) == list:
      newlist = []
      for item in list_or_dict:
        newlist.append(self.sanitize(item))
      return newlist
    elif type(list_or_dict) == dict:
      newdict = {}
      for key in list_or_dict.keys():
        newdict[key] = self.sanitize(list_or_dict[key])
      return newdict
    else:
      return str(list_or_dict)

  def request(self,request):
    """
    Evaluate a statement in the local context

    Note that this only returns strings or standard types, not the user
    defined objects on the server side which they may represent.

    Examples (from the client side):
    >>> ks.request("self.spec[0].LO.get_p('frequency')")
    1300.0
    >>> ks.request("self.IFsw[3].state")
    8

    @param request : command to be evaluated
    @type  request : str

    @return: response
    """
    self.logger.debug("request: processing: %s", request)
    response = eval(request)
    self.logger.debug("request: response was: %s",response)
    if type(response) == str or \
       type(response) == int or \
       type(response) == float or \
       type(response) == bool or \
       type(response) == numpy.ndarray :
      self.logger.debug("request: returns native object")
      return response
    elif type(response) == list or type(response) == dict:
      Pyro_OK = self.sanitize(response)
      self.logger.debug("request: sanitized list or dict %s",Pyro_OK)
      return Pyro_OK
    else:
      self.logger.debug("request: returns str")
      return str(response)

  # ==================== Methods for managing the server ====================

  def running(self):
    """
    Report if the manager is running.  A return value of False should
    not be possible.
    """
    if self.run:
      return True
    else:
      return False

  def halt(self):
    """
    Command to halt the manager
    """
    self.logger.info("halt: Halting")
    self.run = False

class WBDC2hw_server(MCserver, WBDC2hwif):
  def __init__(self, name):
    self.logger = logging.getLogger(module_logger.name+".WBDC2hw_server")
    super(WBDC2hw_server,self).__init__()
    self.logger.debug(" superclass initialized")
    WBDC2hwif.__init__(self, name)
    self.logger.debug(" hardware interface instantiated")
    self.run = True

logpath = "/tmp/" # for now
server_host = "dto.jpl.nasa.gov"

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
     'support':                                       'warning'})

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
  try:
    ns = locator.getNS(host='dto.jpl.nasa.gov')
  except NamingError:
    mylogger.error(
      """Pyro nameserver task not found.
      If pyro-ns is not running. Do 'pyro-ns &'""")
    raise RuntimeError("No Pyro nameserver")
  mylogger.info("Starting %s, please wait....", __name__)
  # Here is the hardware configuration

  m = WBDC2hw_server("WBDC-2")
  mylogger.info("%s started", __name__)
  launch_server(server_host, __name__, m)
  try:
    ns = locator.getNS(host='dto.jpl.nasa.gov')
  except NamingError:
    mylogger.error(
      """Pyro nameserver task notfound. Is the terminal at least 85 chars wide?
      If pyro-ns is not running. Do 'pyro-ns &'""")
    raise RuntimeError("No Pyro nameserver")
  ns.unregister(__name__)
  mylogger.info("%s finished", __name__)
