# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from . import AbstractTestClass

from ansible.modules.identity.ipa.ipa_service import ServiceIPAClient

import os, re

class TestServiceIPAClient(unittest.TestCase, AbstractTestClass):

    test_class = ServiceIPAClient

    # Track state from test to test
    current_state = {}

    find_request = dict(
        method='service_find',
        name=[],
        item=dict(
            all = True,
            krbcanonicalname = 'test/%s@%s' % (
                AbstractTestClass.ipa_host,
                AbstractTestClass.ipa_domain.upper()) ),
    )

    principal = 'test/%s@%s' % (
        AbstractTestClass.ipa_host,
        AbstractTestClass.ipa_domain.upper())
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
        self.runner(
            test_key = 10,
            module_params = dict(
                krbcanonicalname = self.principal,
                usercertificate = self.cert,
                state = "present",
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
                        'item': { 'usercertificate': '%s' % self.cert,
                                  'all': True},
                        'method': 'service_add',
                        'name': [ self.principal ]
                    },
                    reply_updates = {
                        'usercertificate' : self.cert,
                        'managedby_host' : [ self.ipa_host ]},
                ),
                # No enable/disable operation
            ],
        )

    def test_11_service_existing_present_krbticket_flags_1(self):
        self.runner(
            test_key = 11,
            module_params = dict(
                krbcanonicalname = self.principal,
                state = "present",                 # Present:
                ipakrbrequirespreauth = False,     # krbticketflags:  -128
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'item': {'ipakrbrequirespreauth': False,
                                 'all': True},
                        'method': 'service_mod',
                        'name': [ self.principal ],
                    },
                    reply_updates = { 'ipakrbrequirespreauth': False },
                ),
                # No enable/disable operation
            ],
        )

    def test_12_service_existing_present_krbticketflags_2(self):
        self.runner(
            test_key = 12,
            module_params = dict(
                krbcanonicalname = self.principal,
                state = "present",                 # Present:   start: 128
                ipakrbrequirespreauth = True,      # krbticketflags: +128
                ipakrbokasdelegate = True,         # krbticketflags: +1048576
                ipakrboktoauthasdelegate = True,   # krbticketflags: +2097152
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'item': {'ipakrbrequirespreauth': True,
                                 'ipakrbokasdelegate': True,
                                 'ipakrboktoauthasdelegate': True,
                                 'all': True},
                        'method': 'service_mod',
                        'name': [ self.principal ]
                    },
                    reply_updates = { 'ipakrbrequirespreauth': True,
                                      'ipakrbokasdelegate': True,
                                      'ipakrboktoauthasdelegate': True,
                                  },
                ),
                # No enable/disable operation
            ],
        )

    def test_13_service_existing_absent_krbticketflags(self):
        self.runner(
            test_key = 13,
            module_params = dict(
                krbcanonicalname = self.principal,
                state = "absent",                  # Absent
                ipakrbokasdelegate = True,         # To False
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'item': {'ipakrbokasdelegate': False,
                                 'all': True},
                        'method': 'service_mod',
                        'name': [ self.principal ]
                    },
                    reply_updates = { 'ipakrbokasdelegate': False, },
                ),
                # No enable/disable operation
            ],
        )

    def test_14_service_existing_exact_krbticketflags(self):
        self.runner(
            test_key = 14,
            module_params = dict(
                krbcanonicalname = self.principal,
                state = "exact",                    # Exact
                ipakrbrequirespreauth = True,       # Noop
                ipakrbokasdelegate = False,         # Noop
                # ipakrboktoauthasdelegate = False, # To False
                usercertificate = self.cert,        # Noop
                # managedby_host = self.ipa_host    # Remove
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'item': {'ipakrboktoauthasdelegate': False,
                                 'all': True},
                        'method': 'service_mod',
                        'name': [ self.principal ]
                    },
                    reply_updates = { 'ipakrboktoauthasdelegate': False },
                ),
                dict(
                    name = 'remove managedby_host',
                    request = {'item': {'host': [self.ipa_host],
                                        'all': True},
                               'method': 'service_remove_host',
                               'name': [ self.principal ]},
                    reply_updates = { 'managedby_host': [] },
                ),
                # No enable/disable operation
            ],
        )

    def test_15_service_existing_set_managedby(self):
        self.runner(
            test_key = 15,
            module_params = dict(
                krbcanonicalname = self.principal,
                state = "present",                 # Present:
                managedby_host = self.ipa_host,    # Add back ipa_host
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'add managedby_host',
                    request = {
                        'item': {
                            'host': [ self.ipa_host ],
                            'all': True},
                        'method': 'service_add_host',
                        'name': [ self.principal ]
                    },
                    reply_updates = {
                        'managedby_host' : [ self.ipa_host ] },
                ),
                # No enable/disable operation
            ],
        )

    def test_16_service_existing_present_read_write_keytab(self):
        self.runner(
            test_key = 16,
            module_params = dict(
                krbcanonicalname = self.principal,
                state = "present",                           # Present:
                ipaallowedtoperform_write_keys_user = (
                    "admin"),                                # Add uid=admin
                ipaallowedtoperform_write_keys_host = (
                    self.ipa_host),                          # Add fqdn=host1
                ipaallowedtoperform_read_keys_group = (
                    "editors"),                              # Add cn=editors
                ipaallowedtoperform_read_keys_hostgroup = (
                    "ipaservers"),                           # Add cn=ipaservers
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'add create keytab objects to object',
                    request = {
                        'item': {'all': True,
                                 'host': [self.ipa_host],
                                 'user': ['admin']},
                        'method': 'service_allow_create_keytab',
                        'name': [self.principal],
                    },
                    reply_updates = {
                        'ipaallowedtoperform_write_keys_host': [
                            self.ipa_host ],
                        'ipaallowedtoperform_write_keys_user': [
                            'admin' ],
                    },
                ),
                dict(
                    name = 'add retrieve keytab objects to object',
                    request = {
                        'item': {'all': True,
                                 'group': ['editors'],
                                 'hostgroup': ['ipaservers']},
                        'method': 'service_allow_retrieve_keytab',
                        'name': [self.principal],
                    },
                    reply_updates = {
                        'ipaallowedtoperform_read_keys_group': [
                            'editors' ],
                        'ipaallowedtoperform_read_keys_hostgroup': [
                            'ipaservers' ],
                    },
                ),
                # No enable/disable operation
            ],
        )

    def test_17_service_existing_absent_read_write_keytab(self):
        self.runner(
            test_key = 17,
            module_params = dict(
                krbcanonicalname = self.principal,
                state = "absent",                            # Absent:
                ipaallowedtoperform_write_keys_host = (
                    self.ipa_host),                          # Rem host=ipa_host
                ipaallowedtoperform_read_keys_hostgroup = (
                    "ipaservers"),                           # Rem cn=ipaservers
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'remove create keytob objects from object',
                    request = {
                        'item': {'all': True,
                                 'host': [self.ipa_host]},
                        'method': 'service_disallow_create_keytab',
                        'name': [self.principal]},
                    reply_updates = {
                        'ipaallowedtoperform_write_keys_host': [None],
                    },
                ),
                dict(
                    name = 'remove retrieve keytob objects from object',
                    request = {
                        'item': {'all': True,
                                 'hostgroup': ['ipaservers']},
                        'method': 'service_disallow_retrieve_keytab',
                        'name': [self.principal]},
                    reply_updates = {
                        'ipaallowedtoperform_read_keys_hostgroup': [None],
                    },
                ),
                # No enable/disable operation
            ],
        )

    def test_18_service_existing_exact_read_write_keytab(self):
        self.runner(
            test_key = 18,
            module_params = dict(
                krbcanonicalname = self.principal,
                state = "exact",                        # Exact:
                ipaallowedtoperform_read_keys_hostgroup = (
                    "ipaservers"),                      # Add cn=ipaservers
                ipaallowedtoperform_read_keys_group = (
                    "editors"),                         # Noop
                ipaallowedtoperform_write_keys_user = (
                    "admin"),                           # Noop
                managedby_host = self.ipa_host,         # Noop
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'item': {'usercertificate': None,
                                 'all': True},
                        'method': 'service_mod',
                        'name': [self.principal]},
                    reply_updates = {
                        'usercertificate': None,
                    },
                ),
                dict(
                    name = 'add create keytab objects to object',
                    request = {
                        'item': {'hostgroup': ['ipaservers'],
                                 'all': True},
                        'method': 'service_allow_retrieve_keytab',
                        'name': [self.principal],
                    },
                    reply_updates = {
                        'ipaallowedtoperform_read_keys_hostgroup': [
                            'ipaservers' ],
                    },
                ),
                # No enable/disable operation
            ],
        )

    def test_19_service_existing_absent(self):
        self.runner(
            test_key = 19,
            module_params = dict(
                krbcanonicalname = self.principal,
                state = "absent",                     # Absent whole object
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'item': {},
                        'method': 'service_del',
                        'name': [ self.principal ],
                    },
                    reply = {},
                ),
                # No enable/disable operation
            ],
        )


