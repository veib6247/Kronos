#
import unittest

from utils import build_response, convert_timestamp


class UnitTests(unittest.TestCase):
    '''Unit tests for the helper functions'''

    def test_build_response(self):
        '''Tests the "build_response" function'''
        msg: str = 'this is a test string'
        self.assertEqual(
            build_response(True, msg),
            {'status': 'success', 'msg': msg}
        )
        self.assertEqual(
            build_response(False, msg),
            {'status': 'failed', 'msg': msg}
        )

    def test_timestamp_conversion(self):
        '''Tests the "convert_timestamp" function'''
        self.assertEqual(
            convert_timestamp('1727689594'),
            '2024-09-30 17:46:34'
        )
        self.assertEqual(
            convert_timestamp('1727689723'),
            '2024-09-30 17:48:43'
        )


if __name__ == '__main__':
    unittest.main()
