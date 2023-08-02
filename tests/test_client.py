#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. codeauthor:: Cédric Dumay <cedric.dumay@gmail.com>


"""
import unittest
from unittest.mock import patch

from requests import Response

from cdumay_error.types import InternalError
from cdumay_http_client import errors
from cdumay_http_client.client import HttpClient


class TestClient(unittest.TestCase):
    """Tests for http client"""

    def test_init(self):
        """Client inititialization"""
        client = HttpClient(server="http://localhost", timeout=15)
        self.assertEqual(client.server, "http://localhost")
        self.assertEqual(client.timeout, 15)
        self.assertEqual(client.headers, {})
        self.assertIsNone(client.auth)
        self.assertEqual(client.ssl_verify, True)
        self.assertEqual(client.retry_number, 10)
        self.assertEqual(client.retry_delay, 30)
        self.assertEqual(repr(client), 'Connection: http://localhost')

    def test_request_200(self):
        """Test client request"""
        resp = Response()
        resp.status_code = 200
        resp.encoding = 'UTF-8'
        resp._content = b"Hello world"
        with patch('requests.request', return_value=resp):
            client = HttpClient(server="http://localhost", timeout=15)
            data = client.do_request("GET", "/hello")
        self.assertEqual(data, "Hello world")

    def test_request_no_parse(self):
        """Test client request"""
        resp = Response()
        resp.status_code = 200
        resp.encoding = 'UTF-8'
        resp._content = b"Hello world"
        with patch('requests.request', return_value=resp):
            client = HttpClient(server="http://localhost", timeout=15)
            data = client.do_request("GET", "/hello", parse_output=False)
        self.assertIsInstance(data, Response)

    def test_no_retry(self):
        """Test no retry on error"""
        with self.assertRaises(errors.InternalServerError) as context:
            client = HttpClient(server="htp:/localhost", timeout=1)
            client.do_request(
                "GET", "/hello", no_retry_on=[errors.InternalServerError]
            )

        self.assertEqual(context.exception.code, 500)
        self.assertEqual(context.exception.MSGID, "HTTP-02752")
        self.assertIsInstance(context.exception, errors.InternalServerError)
        self.assertEqual(context.exception.message, "Internal Server Error")
        self.assertEqual(context.exception.extra, {
            'url': "htp:/localhost/hello",
            'server': "htp:/localhost",
            'method': "GET"
        })

    def test_500(self):
        """Test 500 error"""
        with self.assertRaises(errors.InternalServerError) as context:
            client = HttpClient(
                server="htp:/localhost",
                timeout=1,
                retry_number=1,
                retry_delay=1
            )
            client.do_request("GET", "/hello")

        self.assertEqual(context.exception.code, 500)
        self.assertEqual(context.exception.MSGID, "HTTP-02752")
        self.assertIsInstance(context.exception, errors.InternalServerError)
        self.assertEqual(context.exception.message, "Internal Server Error")
        self.assertEqual(context.exception.extra, {
            'url': "htp:/localhost/hello",
            'server': "htp:/localhost",
            'method': "GET"
        })

    def test_empty_response(self):
        """Empty response"""
        with patch('requests.request', return_value=None), \
                self.assertRaises(errors.MisdirectedRequest) as context:
            client = HttpClient(
                server="http://localhost",
                timeout=1,
                retry_number=1,
                retry_delay=1
            )
            client.do_request("POST", "/hello")

        self.assertEqual(context.exception.code, 421)
        self.assertEqual(context.exception.MSGID, "HTTP-24099")
        self.assertIsInstance(context.exception, errors.MisdirectedRequest)
        self.assertEqual(context.exception.message, "Misdirected Request")
        self.assertEqual(context.exception.extra, {
            'url': "http://localhost/hello",
            'server': "http://localhost",
            'method': "POST"
        })

    def test_3xx(self):
        resp = Response()
        resp.status_code = 301
        resp.encoding = 'UTF-8'
        resp._content = b"Error: Moved Permanently"
        with patch('requests.request', return_value=resp), \
                self.assertRaises(errors.MovedPermanently) as context:
            client = HttpClient(
                server="http://localhost",
                timeout=1,
                retry_number=1,
                retry_delay=1
            )
            client.do_request("GET", "/hello")

        self.assertEqual(context.exception.code, 301)
        self.assertEqual(context.exception.MSGID, "HTTP-30785")
        self.assertIsInstance(context.exception, errors.MovedPermanently)
        self.assertEqual(context.exception.message, "Error: Moved Permanently")
        self.assertEqual(context.exception.extra, {
            'headers': {},
            'url': "http://localhost/hello",
            'server': "http://localhost",
            'payload': None,
            'request_id': None,
            'response': 'Error: Moved Permanently',
            'method': "GET"
        })

    def test_unexpected_error(self):
        """Test unexpected error"""
        with self.assertRaises(InternalError) as context:
            client = HttpClient(
                server="http://localhost",
                timeout=1,
                retry_number=-1,
                retry_delay=1
            )
            client.do_request("GET", "/hello")

        self.assertEqual(context.exception.code, 500)
        self.assertEqual(context.exception.MSGID, "ERR-29885")
        self.assertIsInstance(context.exception, InternalError)
        self.assertEqual(
            context.exception.message,
            "Unexcepected error, failed to perform request 'GET' on "
            "'http://localhost/hello' after -1 retries"
        )
        self.assertEqual(context.exception.extra, {
            'url': "http://localhost/hello",
            'server': "http://localhost",
            'method': "GET"
        })
