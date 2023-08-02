#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. codeauthor:: Cédric Dumay <cedric.dumay@gmail.com>


"""
import unittest

from cdumay_error import Error
from cdumay_http_client import errors
from cdumay_http_client.errors import from_status


class TestError(unittest.TestCase):
    """Tests for class Error"""

    def test_from_status(self):
        """Test error from HTTP status"""
        err = from_status(
            404, "Error: Not Found", extra={'url': "http://localhost"}
        )
        self.assertIsInstance(err, errors.NotFound)
        self.assertEqual(err.message, "Error: Not Found")
        self.assertEqual(err.extra, {'url': "http://localhost"})

        unknown_error = from_status(3600)
        self.assertIsInstance(unknown_error, Error)
        self.assertEqual(unknown_error.message, "Unknown Error")
        self.assertEqual(unknown_error.extra, {})

    def test_from_response(self):
        """"""
