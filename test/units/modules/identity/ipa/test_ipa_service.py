# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from . import AbstractTestClass

from ansible.modules.identity.ipa.ipa_service import ServiceIPAClient

class TestServiceIPAClient(unittest.TestCase, AbstractTestClass):

    test_class = ServiceIPAClient

    # Track state from test to test
    current_state = {}

    find_request = dict(
        method='service_find',
        name=[None],
        item=dict(all = True,
                  krbcanonicalname = 'test/host1.example.com@EXAMPLE.COM' ),
        item_filter=None,
    )

    cert = ("MIICjDCCAfWgAwIBAgIJALTKa/IEGbmsMA0GCSqGSIb3DQEBCwUAMF8xCzAJ"
            "BgNVBAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRl"
            "cm5ldCBXaWRnaXRzIFB0eSBMdGQxGDAWBgNVBAMMD2gwMS56dWx0cm9uLmNv"
            "bTAeFw0xNzA1MDEwMDIwNDVaFw0xODA1MDEwMDIwNDVaMF8xCzAJBgNVBAYT"
            "AkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX"
            "aWRnaXRzIFB0eSBMdGQxGDAWBgNVBAMMD2gwMS56dWx0cm9uLmNvbTCBnzAN"
            "BgkqhkiG9w0BAQEFAAOBjQAwgYkCgYEAulxki2+gnPCm+UYtVrv94OFeYhwq"
            "2rfVya5AvRYiTvxOHSNxrRvmwYMtWM8wFCwtZYb3Ts/m+0I/INZEY8Drhiyk"
            "qIlY+vcqPvgGJb7UeEtzRPFOc8WIIyKz8rJGPIptJ9cqjr6cSXE2rF0YIfTj"
            "rJNBz9L8vHMaPzoa8EiccrsCAwEAAaNQME4wHQYDVR0OBBYEFOGzxEOnQ/XK"
            "zL6kdK5f6qga7Xd0MB8GA1UdIwQYMBaAFOGzxEOnQ/XKzL6kdK5f6qga7Xd0"
            "MAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcNAQELBQADgYEAVWIsphw/pmAk8Fh+"
            "51Bat7W4ix2BzmB1F4aLskqkIZvh5KJQdB2stdmrA+FiuyfUHXmJQEzDEgmn"
            "xViVSZvRDAWedoD0fxC0zq+YBpHNk6k4F3wk8ccs61UcTT9sSF2XCyTPY2Dp"
            "h5t2NjIPnok21M9poZQuvV39ExKRgoIQLnA=")

    # Show long diffs incl. cert
    maxDiff = 3000

    def test_10_service_present_new(self):
        test = 10
        # Create new object
        client = self.runner(
            module_params = dict(
                krbcanonicalname = "test/host1.example.com@EXAMPLE.COM",
                certificate = self.cert,
                state = "present",
                ipa_host = "host1.example.com",
                ipa_user = "admin",
                ipa_pass = "secretpass",
            ),
            post_json_calls = [
                dict(
                    name = 'find new object',
                    request = self.find_request,
                    reply = {},
                ),
                dict(
                    name = 'add new object',
                    request = {
                        'item': {'setattr': [ 'certificate=%s' % self.cert ],
                                 'addattr': [], 'delattr': [], 'all': True},
                        'item_filter': None,
                        'method': 'service_add',
                        'name': [ 'test/host1.example.com@EXAMPLE.COM' ] },
                    reply_updates = {
                        'certificate' : self.cert },
                ),
                # No enable/disable operation
            ],
        )

        # Persist client between tests
        self.current_state['client%d' % test] = client

    def test_11_service_existing_present_krbticket_flags_1(self):
        test = 11
        client = self.runner(
            module_params = dict(
                krbcanonicalname = "test/host1.example.com@EXAMPLE.COM",
                state = "present",                 # Present:
                ipakrbrequirespreauth = True,      # krbticketflags:  +128
                ipa_host = "host1.example.com",
                ipa_user = "admin",
                ipa_pass = "secretpass",
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                    reply = self.current_state['client%d' % (test-1)].final_obj,
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'item': {'setattr': [ 'krbticketflags=128' ],
                                 'addattr': [], 'delattr': [], 'all': True},
                        'item_filter': None,
                        'method': 'service_mod',
                        'name': [ 'test/host1.example.com@EXAMPLE.COM' ]
                    },
                    reply_updates = { 'krbticketflags': [ 128 ] },
                ),
                # No enable/disable operation
            ],
        )

        # Persist client between tests
        self.current_state['client%d' % test] = client

    def test_12_service_existing_present_krbticketflags_2(self):
        test = 12
        client = self.runner(
            module_params = dict(
                krbcanonicalname = "test/host1.example.com@EXAMPLE.COM",
                state = "present",                 # Present:   start: 128
                ipakrbrequirespreauth = False,     # krbticketflags: -128
                ipakrbokasdelegate = True,         # krbticketflags: +1048576
                ipakrboktoauthasdelegate = True,   # krbticketflags: +2097152
                ipa_host = "host1.example.com",
                ipa_user = "admin",
                ipa_pass = "secretpass",
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                    reply = self.current_state['client%d' % (test-1)].final_obj,
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'item': {'setattr': [ 'krbticketflags=3145728' ],
                                 'addattr': [], 'delattr': [], 'all': True},
                        'item_filter': None,
                        'method': 'service_mod',
                        'name': [ 'test/host1.example.com@EXAMPLE.COM' ]
                    },
                    reply_updates = { 'krbticketflags': [ 3145728 ] },
                ),
                # No enable/disable operation
            ],
        )

        # Persist client between tests
        self.current_state['client%d' % test] = client

    def test_13_service_existing_absent_krbticketflags(self):
        test = 13
        client = self.runner(
            module_params = dict(
                krbcanonicalname = "test/host1.example.com@EXAMPLE.COM",
                state = "absent",                  # Absent:   start: 3145728
                ipakrbrequirespreauth = False,     # krbticketflags: Noop
                ipakrbokasdelegate = True,         # krbticketflags: -1048576
                ipakrboktoauthasdelegate = False,  # krbticketflags: Noop
                ipa_host = "host1.example.com",
                ipa_user = "admin",
                ipa_pass = "secretpass",
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                    reply = self.current_state['client%d' % (test-1)].final_obj,
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'item': {'setattr': [ 'krbticketflags=%d' % 2097152 ],
                                 'addattr': [], 'delattr': [], 'all': True},
                        'item_filter': None,
                        'method': 'service_mod',
                        'name': [ 'test/host1.example.com@EXAMPLE.COM' ]
                    },
                    reply_updates = { 'krbticketflags': 2097152 },
                ),
                # No enable/disable operation
            ],
        )

        # Persist client between tests
        self.current_state['client%d' % test] = client

    def test_14_service_existing_exact_krbticketflags(self):
        test = 13
        client = self.runner(
            module_params = dict(
                krbcanonicalname = "test/host1.example.com@EXAMPLE.COM",
                state = "exact",                   # Exact:  start 2097152
                ipakrbrequirespreauth = True,      # krbticketflags: +128
                ipakrbokasdelegate = False,        # krbticketflags: Noop
                ipakrboktoauthasdelegate = True,   # krbticketflags: Same
                certificate = self.cert,           # Same
                ipa_host = "host1.example.com",
                ipa_user = "admin",
                ipa_pass = "secretpass",
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                    reply = self.current_state['client%d' % (test-1)].final_obj,
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'item': {'setattr': [ 'krbticketflags=2097280' ],
                                 'addattr': [], 'delattr': [], 'all': True},
                        'item_filter': None,
                        'method': 'service_mod',
                        'name': [ 'test/host1.example.com@EXAMPLE.COM' ]
                    },
                    reply_updates = { 'krbticketflags': [ 2097280 ] },
                ),
                # No enable/disable operation
            ],
        )

        # Persist client between tests
        self.current_state['client%d' % test] = client

    def test_15_service_existing_set_managedby(self):
        test = 13
        client = self.runner(
            module_params = dict(
                krbcanonicalname = "test/host1.example.com@EXAMPLE.COM",
                state = "present",                 # Present:
                host = "host1.example.com",        # Add host1
                directory_base_dn = 'dc=example,dc=com',
                ipa_host = "host1.example.com",
                ipa_user = "admin",
                ipa_pass = "secretpass",
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                    reply = self.current_state['client%d' % (test-1)].final_obj,
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'item': {
                            'addattr': [ (
                                'managedby=fqdn=host1.example.com,cn=computers,'
                                'cn=accounts,dc=example,dc=com') ],
                            'setattr': [], 'delattr': [], 'all': True},
                        'item_filter': None,
                        'method': 'service_mod',
                        'name': [ 'test/host1.example.com@EXAMPLE.COM' ]
                    },
                    reply_updates = {
                        'managedby' : [ 'fqdn=host1.example.com,cn=computers,'
                                        'cn=accounts,dc=example,dc=com' ] },
                ),
                # No enable/disable operation
            ],
        )

        # Persist client between tests
        self.current_state['client%d' % test] = client

