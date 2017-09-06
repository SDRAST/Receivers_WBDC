import logging
import unittest
import threading

import Pyro4
import Pyro4.socketutil
import Pyro4.naming

import pyro4tunneling

from wbdc2hw_pyro4_server import WBDC2hwServer

class TestWBDCServer(unittest.TestCase):

    isSetup = False
    server = None
    client = None

    def setUp(self):
        if not self.__class__.isSetup:

            port = Pyro4.socketutil.findProbablyUnusedPort()
            ns_details = Pyro4.naming.startNS(port=port)
            ns_thread = threading.Thread(target=ns_details[1].requestLoop)
            ns_thread.daemon = True
            ns_thread.start()

            res = pyro4tunneling.util.check_connection(Pyro4.locateNS, kwargs={"port":port})
            ns = Pyro4.locateNS(port=port)

            name = "wbdc2hw_pyro4_server"
            logger = logging.getLogger(name)
            logger.setLevel(logging.DEBUG)
            server = WBDC2hwServer(name, logger=logger)
            server_thread = server.launch_server(ns_port=port, local=True, threaded=True)

            self.__class__.client = Pyro4.Proxy(ns.lookup(server.name))
            self.__class__.server = server
            self.__class__.isSetup = True

        else:
            pass

    def test_get_atten_IDs(self):
        client = self.__class__.client
        result = client.get_atten_IDs()
        self.assertTrue(isinstance(result, list))

    def test_set_atten_volts(self):
        client = self.__class__.client

    def test_get_atten_volts(self):
        client = self.__class__.client
        result = client.get_atten_volts('R1-18-E')
        self.assertIsNotNone(result)

    def test_set_atten(self):
        client = self.__class__.client

    def test_get_atten(self):
        client = self.__class__.client
        result = client.get_atten('R1-18-E')
        self.assertIsNotNone(result)

    def test_get_monitor_data(self):
        client = self.__class__.client
        result = client.get_monitor_data()
        self.assertIsNotNone(result)

    def test_set_crossover(self):
        client = self.__class__.client

    def test_get_crossover(self):
        client = self.__class__.client
        result = client.get_crossover()
        self.assertIsNotNone(result)

    def test_set_polarizers(self):
        client = self.__class__.client

    def test_get_polarizers(self):
        client = self.__class__.client
        result = client.get_polarizers()
        self.assertIsNotNone(result)

    def test_sideband_separation(self):
        client = self.__class__.client

    def test_get_IF_hybrids(self):
        client = self.__class__.client
        result = client.get_IF_hybrids()
        self.assertIsNotNone(result)

if __name__ == '__main__':
    logging.basicConfig(loglevel=logging.DEBUG)
    suite_get = unittest.TestSuite()
    suite_set = unittest.TestSuite()

    suite_get.addTest(TestWBDCServer("test_get_atten_IDs"))
    suite_get.addTest(TestWBDCServer("test_get_atten_volts"))
    suite_get.addTest(TestWBDCServer("test_get_atten"))
    suite_get.addTest(TestWBDCServer("test_get_monitor_data"))
    suite_get.addTest(TestWBDCServer("test_get_crossover"))
    suite_get.addTest(TestWBDCServer("test_get_polarizers"))
    suite_get.addTest(TestWBDCServer("test_get_IF_hybrids"))

    suite_set.addTest(TestWBDCServer("test_set_atten_volts"))
    suite_set.addTest(TestWBDCServer("test_set_atten"))
    suite_set.addTest(TestWBDCServer("test_set_crossover"))
    suite_set.addTest(TestWBDCServer("test_set_polarizers"))
    suite_set.addTest(TestWBDCServer("test_sideband_separation"))

    result_get = unittest.TextTestRunner().run(suite_get)
    if result_get.wasSuccessful():
        unittest.TextTestRunner().run(suite_set)
