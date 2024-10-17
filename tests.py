#
import unittest

from utils import build_response, convert_timestamp


class UnitTests(unittest.TestCase):
    '''Unit tests for the helper functions'''

    test_string: str = 'this is a test string'

    #
    def test_build_response_success(self):
        '''Asserts a success response in the "build_response" function'''
        self.assertEqual(
            build_response(True, self.test_string),
            {'status': 'success', 'msg': self.test_string}
        )

    #
    def test_build_response_failed(self):
        '''Asserts a failed response in the "build_response" function'''
        self.assertEqual(
            build_response(False, self.test_string),
            {'status': 'failed', 'msg': self.test_string}
        )

    #
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
