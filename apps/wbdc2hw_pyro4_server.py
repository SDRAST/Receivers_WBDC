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
import argparse
import logging
import sys
import os

import Pyro5

from local_dirs import log_dir
from MonitorControl.Receivers.WBDC.WBDC2.WBDC2hwif import WBDC2hwif
from supprt.pyro.pyro5_support import Pyro5Server

module_logger = logging.getLogger(__name__)

@Pyro5.api.expose
class WBDC2hwServer(Pyro4Server):
    """
    Server for interfacing with the Wide Band Down Converter2
    """
    def __init__(self, name, logger=None, **kwargs):
        """
        """
        if not logger:
            logger = logging.getLogger(module_logger.name + ".WBDC2hw_server")
        Pyro5Server.__init__(self, name=name, logger=logger, **kwargs)
        self.logger.debug("Pyro4Server superclass initialized")
        self.wbdc = WBDC2hwif(name)
        self.logger.debug("hardware interface superclass instantiated")

    def set_WBDC(self, option):
        """
        Emulate old WBDC1 server
        """
        self.logger.debug("set_WBDC: Called. Option: {}".format(option))
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
        self.logger.debug("get_atten_IDs: Called.")
        report = []
        for ps in self.wbdc.pol_sec.keys():
            for att in self.wbdc.pol_sec[ps].atten.keys():
                report.append(att)
        report.sort()
        self.logger.debug("get_atten_IDs: report: {}".format(report))
        return report

    def set_atten_volts(self, ID, V):
        """
        Sets the designated attenuator voltage
        """
        self.logger.debug("set_atten_volts: Called. ID: {}, V: {}".format(ID, V))
        pol_id = ID[:5]
        self.logger.debug("set_atten: pol section is %s", pol_id)
        self.wbdc.pol_sec[pol_id].atten[ID].VS.setVoltage(V)
        return True

    def get_atten_volts(self, ID):
        """
        Return attenuator voltage

        The voltage source remembers the last requested voltage.  If voltage has
        not been set, it is the default of 0 V.
        """
        self.logger.debug("get_atten_volts: Called. ID: {}".format(ID))
        pol_id = ID[:5]
        volts = self.wbdc.pol_sec[pol_id].atten[ID].VS.volts
        if not volts:
            volts = 0.0
            self.wbdc.pol_sec[pol_id].atten[ID].VS.volts = volts
        self.logger.debug("get_atten_volts: volts: {}".format(volts))
        return volts

    def set_atten(self, ID, dB):
        """
        Sets pol section quad hybrid input attentuator

        @param ID : attenuator identifier
        @type  ID : str

        @param atten : requested attenuation
        @type  atten : float
        """
        self.logger.debug("set_atten: Called. ID: {}, dB: {}".format(ID, dB))
        pol_id = ID[:5]
        self.logger.debug("set_atten: pol section is {}".format(pol_id))
        self.wbdc.pol_sec[pol_id].atten[ID].set_atten(dB)
        return self.wbdc.pol_sec[pol_id].atten[ID].atten

    def get_atten(self, ID):
        """
        Returns the attenuation to which the specified attenuator is set.

        This does not query the hardware.  The attenuator simply remembers the last
        requested attenuation.  If 'set_atten' has not been used, it rteurns a
        blank.
        """
        self.logger.debug("get_atten: Called. ID: {}".format(ID))
        pol_id = ID[:5]
        self.logger.debug("get_atten: pol section is {}".format(pol_id))
        result = self.wbdc.pol_sec[pol_id].atten[ID].get_atten()
        self.logger.debug("get_atten: result {}".format(result))
        return result

    def get_monitor_data(self):
        """
        Returns the analog voltages, currents and temperatures
        """
        self.logger.debug("get_monitor_data: Called.")
        monitor_data = {}
        for latchgroup in [1, 2]:
            MD = self.wbdc.analog_monitor.get_monitor_data(latchgroup)
            for key in MD.keys():
                monitor_data[key] = MD[key]
        self.logger.debug("get_monitor_data: monitor_data: {}".format(monitor_data))
        return monitor_data

    def set_crossover(self, crossover):
        """
        Set or unset the crossover switch
        """
        self.logger.debug("set_crossover: Called. crossover: {}".format(crossover))
        result = self.wbdc.crossSwitch.set_state(crossover)
        self.logger.debug("set_crossover: result: {}".format(result))
        return result

    def get_crossover(self):
        """
        Set or unset the crossover switch
        """
        self.logger.debug("get_crossover: Called.")
        state = self.wbdc.crossSwitch.get_state()
        self.logger.debug("get_crossover: state: {}".format(state))
        return state

    def set_polarizers(self, state):
        """
        Set all polarizers to the specified state

        True for E/H to L/R conversion.  Flase for bypass.
        """
        self.logger.debug("set_polarizers: Called. state: {}".format(state))
        states = {}
        for ps in self.wbdc.pol_sec.keys():
            states[ps] = self.wbdc.pol_sec[ps].set_state(state)
        self.logger.debug("set_polarizers: states: {}".format(states))
        return states

    def get_polarizers(self):
        """
        Set all polarizers to the specified state

        True for E/H to L/R conversion.  Flase for bypass.
        """
        self.logger.debug("get_polarizers: Called.")
        states = {}
        for ps in self.wbdc.pol_sec.keys():
            states[ps] = self.wbdc.pol_sec[ps].get_state()
        self.logger.debug("get_polarizers: states: {}".format(states))
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
        self.logger.debug("sideband_separation: Called. state: {}".format(state))
        states = {}
        for dc in self.wbdc.DC.keys():
            states[dc] = self.wbdc.DC[dc].set_state(1 - int(state))
        self.logger.debug("sideband_separation: states: {}".format(states))
        return states

    def get_IF_hybrids(self):
        """
        Returns the state of the IQ-to-LU hybrids.

        True means that the hybrid is bypassed, False that it is engaged.
        """
        self.logger.debug("get_IF_hybrids: Called.")
        states = {}
        for dc in self.wbdc.DC.keys():
            states[dc] = self.wbdc.DC[dc].get_state()
        self.logger.debug("get_IF_hybrids: states: {}".format(states))
        return states

def simple_parse_args():
    """
    """
    parser = argparse.ArgumentParser(description="Start WBDC-2 Pyro4 server")

    parser.add_argument('--remote_server_name', '-rsn',
                        dest='remote_server_name',
                        action='store', 
                        default='localhost', 
                        type=str, 
                        required=False,
                        help="Specify the name of the remote host. If you're"+
                        " trying to access a Pyro nameserver that is running"+
                        " locally, then use localhost. If you supply a value"+
                        " other than 'localhost'then make sure to give other"+
                        " remote login information.")

    parser.add_argument('--remote_port', '-rp', 
                        dest='remote_port',
                        action='store', 
                        type=int, 
                        required=False, 
                        default=None,
                        help="""Specify the remote port.""")

    parser.add_argument("--ns_host", "-nsn", 
                        dest='ns_host', 
                        action='store', 
                        default='localhost',
                        help="Specify a host name for the Pyro name server."+
                        " Default is localhost")

    parser.add_argument("--ns_port", "-nsp",
                        dest='ns_port', 
                        action='store',
                        default=50000,
                        type=int,
                        help="Specify a port number for the Pyro name server."+
                        " Default is 50000.")

    parser.add_argument("--simulated", "-s",
                        dest='simulated', 
                        action='store_true', 
                        default=False,
                        help="Specify whether or not the server is running in"+
                        " simulator mode.")

    parser.add_argument("--local", "-l",
                        dest='local', 
                        action='store_true', 
                        default=False,
                        help="Specify whether or not the server is running"+
                        " locally or on a remote server.")

    parser.add_argument("--verbose", "-v",
                        dest="verbose", 
                        action='store_true', 
                        default=False,
                        help="Specify whether not the loglevel should be DEBUG")
    return parser

def setup_logging(logfile, level):
    """
    Setup logging.
    Args:
        logfile (str): The path to the logfile to use.
    Returns:
        None
    """
    logging.basicConfig(level=level)
    s_formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    f_formatter = logging.Formatter(
                               '%(levelname)s:%(asctime)s:%(name)s:%(message)s')

    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(f_formatter)

    sh = logging.StreamHandler()
    sh.setLevel(level)
    sh.setFormatter(s_formatter)

    root_logger = logging.getLogger('')
    root_logger.handlers = []
    root_logger.addHandler(fh)
    root_logger.addHandler(sh)

if __name__ == "__main__":
    from socket import gethostname
    import datetime

    parsed = simple_parse_args().parse_args()
    name = 'wbdc2hw_pyro4_server-'+gethostname()

    if parsed.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    #logpath = "/usr/local/logs"
    timestamp = datetime.datetime.utcnow().strftime("%j-%Hh%Mm")
    logfile = os.path.join(log_dir,"{}_{}.log".format(name, timestamp))

    setup_logging(logfile, loglevel)
    logger = logging.getLogger(name)
    logger.setLevel(loglevel)

    m = WBDC2hwServer(name, logfile=logfile, logger=logger)
    m.launch_server(remote_server_name=parsed.remote_server_name,
                    local=parsed.local,
                    ns_host=parsed.ns_host,
                    ns_port=parsed.ns_port,
                    objectId=equipment["Antenna"].name,
                    objectPort=50003, 
                    ns=False, 
                    threaded=False, 
                    local=True)
