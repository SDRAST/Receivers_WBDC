"""
Testing just through the WBDC
"""
from MonitorControl.Configurations import station_configuration
from MonitorControl.config_test import *
from support import logs
                                     
if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  testlogger = logging.getLogger()
  testlogger = logs.init_logging(testlogger, loglevel=logging.DEBUG,
                                 consolevel=logging.DEBUG)
  
  observatory, equipment = station_configuration('wbdc2')
  receiver = equipment['Receiver']
  receiver.set_IF_mode(SB_separated=True)
