from support.test import AutoTestSuite
from support.logs import setup_logging

from MonitorControl.Receivers.WBDC.WBDC2 import WBDC2

auto_tester = AutoTestSuite(WBDC2, args=("WBDC-2",))
suite, test_cls_factory = auto_tester.create_test_suite(factory=True)

class TestWBDC2(test_cls_factory()):
    pass

if __name__ == '__main__':
    setup_logging(logLevel=logging.DEBUG)
    unittest.main()
