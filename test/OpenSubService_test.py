import unittest

from .context import service


TEST_HASH = '92099e543d2a0841'

class OpenSubServiceTests(unittest.TestCase):
    def setUp(self):
        pass

    def test_calculate_hash(self):
        pass

    def test_download_by_hash(self):
        svc = service.OpenSubService()
        svc.download_by_hash(TEST_HASH, lambda x: print(str(x)))
    