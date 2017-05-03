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
        self.runner(
            test_key = 10,
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
                        'method': 'service_add',
                        'name': [ 'test/host1.example.com@EXAMPLE.COM' ] },
                    reply_updates = {
                        'certificate' : self.cert },
                ),
                # No enable/disable operation
            ],
        )

    def test_11_service_existing_present_krbticket_flags_1(self):
        self.runner(
            test_key = 11,
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
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'item': {'setattr': [ 'krbticketflags=128' ],
                                 'addattr': [], 'delattr': [], 'all': True},
                        'method': 'service_mod',
                        'name': [ 'test/host1.example.com@EXAMPLE.COM' ]
                    },
                    reply_updates = { 'krbticketflags': [ 128 ] },
                ),
                # No enable/disable operation
            ],
        )

    def test_12_service_existing_present_krbticketflags_2(self):
        self.runner(
            test_key = 12,
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
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'item': {'setattr': [ 'krbticketflags=3145728' ],
                                 'addattr': [], 'delattr': [], 'all': True},
                        'method': 'service_mod',
                        'name': [ 'test/host1.example.com@EXAMPLE.COM' ]
                    },
                    reply_updates = { 'krbticketflags': [ 3145728 ] },
                ),
                # No enable/disable operation
            ],
        )

    def test_13_service_existing_absent_krbticketflags(self):
        self.runner(
            test_key = 13,
            module_params = dict(
                krbcanonicalname = "test/host1.example.com@EXAMPLE.COM",
                state = "absent",                  # Absent:   start: 3145728
                ipakrbokasdelegate = True,         # krbticketflags: -1048576
                ipa_host = "host1.example.com",
                ipa_user = "admin",
                ipa_pass = "secretpass",
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'item': {'setattr': [ 'krbticketflags=%d' % 2097152 ],
                                 'addattr': [], 'delattr': [], 'all': True},
                        'method': 'service_mod',
                        'name': [ 'test/host1.example.com@EXAMPLE.COM' ]
                    },
                    reply_updates = { 'krbticketflags': [ 2097152 ] },
                ),
                # No enable/disable operation
            ],
        )

    def test_14_service_existing_exact_krbticketflags(self):
        self.runner(
            test_key = 14,
            module_params = dict(
                krbcanonicalname = "test/host1.example.com@EXAMPLE.COM",
                state = "exact",                   # Exact:  start 2097152
                ipakrbrequirespreauth = True,      # krbticketflags: +128
                ipakrbokasdelegate = False,        # krbticketflags: Noop
                # ipakrboktoauthasdelegate = True, # krbticketflags: -2097152
                certificate = self.cert,           # Same
                ipa_host = "host1.example.com",
                ipa_user = "admin",
                ipa_pass = "secretpass",
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'item': {'setattr': [ 'krbticketflags=128' ],
                                 'addattr': [], 'delattr': [], 'all': True},
                        'method': 'service_mod',
                        'name': [ 'test/host1.example.com@EXAMPLE.COM' ]
                    },
                    reply_updates = { 'krbticketflags': [ 128 ] },
                ),
                # No enable/disable operation
            ],
        )

    def test_15_service_existing_set_managedby(self):
        self.runner(
            test_key = 15,
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
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'item': {
                            'addattr': [ (
                                'managedby=fqdn=host1.example.com,cn=computers,'
                                'cn=accounts,dc=example,dc=com') ],
                            'setattr': [], 'delattr': [], 'all': True},
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

    def test_16_service_existing_present_read_write_keytab(self):
        self.runner(
            test_key = 16,
            module_params = dict(
                krbcanonicalname = "test/host1.example.com@EXAMPLE.COM",
                state = "present",                           # Present:
                write_keytab_users = "admin",                # Add uid=admin
                write_keytab_hosts = ["host1.example.com",   # Add fqdn=host1
                                      "host2.example.com",   # Add fqdn=host2
                                      "host3.example.com"],  # Add fqdn=host3
                read_keytab_groups = "editors",              # Add cn=editors
                read_keytab_hostgroups = "hg1",              # Add cn=hg1
                directory_base_dn = 'dc=example,dc=com',
                ipa_host = "host1.example.com",
                ipa_user = "admin",
                ipa_pass = "secretpass",
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'item': {
                            'addattr': [
                                ('ipaallowedtoperform;read_keys='
                                 'cn=editors,cn=groups,'
                                 'cn=accounts,dc=example,dc=com'),
                                ('ipaallowedtoperform;read_keys='
                                 'cn=hg1,cn=hostgroups,'
                                 'cn=accounts,dc=example,dc=com'),
                                ('ipaallowedtoperform;write_keys='
                                 'fqdn=host1.example.com,cn=computers,'
                                 'cn=accounts,dc=example,dc=com'),
                                ('ipaallowedtoperform;write_keys='
                                 'fqdn=host2.example.com,cn=computers,'
                                 'cn=accounts,dc=example,dc=com'),
                                ('ipaallowedtoperform;write_keys='
                                 'fqdn=host3.example.com,cn=computers,'
                                 'cn=accounts,dc=example,dc=com'),
                                ('ipaallowedtoperform;write_keys='
                                 'uid=admin,cn=users,'
                                 'cn=accounts,dc=example,dc=com'),
                            ],
                            'setattr': [], 'delattr': [], 'all': True},
                        'method': 'service_mod',
                        'name': [ 'test/host1.example.com@EXAMPLE.COM' ]
                    },
                    reply_updates = {
                        'ipaallowedtoperform;write_keys': [
                            ( 'uid=admin,cn=users,'
                              'cn=accounts,dc=example,dc=com'),
                            ( 'fqdn=host1.example.com,cn=computers,'
                              'cn=accounts,dc=example,dc=com'),
                            ( 'fqdn=host2.example.com,cn=computers,'
                              'cn=accounts,dc=example,dc=com'),
                            ( 'fqdn=host3.example.com,cn=computers,'
                              'cn=accounts,dc=example,dc=com')],
                        'ipaallowedtoperform;read_keys': [
                            ( 'cn=editors,cn=groups,'
                              'cn=accounts,dc=example,dc=com'),
                            ( 'cn=hg1,cn=hostgroups,'
                              'cn=accounts,dc=example,dc=com')],
                    },
                ),
                # No enable/disable operation
            ],
        )

    def test_17_service_existing_absent_read_write_keytab(self):
        self.runner(
            test_key = 17,
            module_params = dict(
                krbcanonicalname = "test/host1.example.com@EXAMPLE.COM",
                state = "absent",                            # Absent:
                write_keytab_hosts = ["host1.example.com",   # Del fqdn=host1
                                      "host4.example.com"],  # Noop
                read_keytab_groups = "editors",              # Del cn=editors
                directory_base_dn = 'dc=example,dc=com',
                ipa_host = "host1.example.com",
                ipa_user = "admin",
                ipa_pass = "secretpass",
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'item': {
                            'addattr': [
                                
                            ],
                            'delattr': [
                                ('ipaallowedtoperform;read_keys='
                                 'cn=editors,cn=groups,'
                                 'cn=accounts,dc=example,dc=com'),
                                ('ipaallowedtoperform;write_keys='
                                 'fqdn=host1.example.com,cn=computers,'
                                 'cn=accounts,dc=example,dc=com'),
                            ],
                            'setattr': [], 'all': True},
                        'method': 'service_mod',
                        'name': [ 'test/host1.example.com@EXAMPLE.COM' ]
                    },
                    reply_updates = {
                        'ipaallowedtoperform;write_keys': [
                            ( 'fqdn=host2.example.com,cn=computers,'
                              'cn=accounts,dc=example,dc=com'),
                            ( 'fqdn=host3.example.com,cn=computers,'
                              'cn=accounts,dc=example,dc=com'),
                            ( 'uid=admin,cn=users,'
                              'cn=accounts,dc=example,dc=com')],
                        'ipaallowedtoperform;read_keys': [
                            ( 'cn=hg1,cn=hostgroups,'
                              'cn=accounts,dc=example,dc=com')],
                    },
                ),
                # No enable/disable operation
            ],
        )

    def test_18_service_existing_exact_read_write_keytab(self):
        self.runner(
            test_key = 18,
            module_params = dict(
                krbcanonicalname = "test/host1.example.com@EXAMPLE.COM",
                state = "exact",                     # Exact:
                read_keytab_hostgroups = ["hg1",     # Keep read hostgroup hg1
                                          "hg2"],    # Add read  hostgroup hg2
                read_keytab_groups = "editors",      # Add read group editors
                write_keytab_users = "admin",        # Keep write user admin
                # write_keytab_hosts = ["host2",     # Del write host host2
                #                       "host3"],    # Del write host host3
                # ipakrbrequirespreauth = True,      # krbticketflags: 0
                # ipakrboktoauthasdelegate = True,
                host = "host2.example.com",         # Add managedby host2
                # host = "host1.example.com",       # Del managedby host1
                # certificate = self.cert,           # Del certificate

                directory_base_dn = 'dc=example,dc=com',
                ipa_host = "host1.example.com",
                ipa_user = "admin",
                ipa_pass = "secretpass",
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'item': {
                            'setattr': [
                                'krbticketflags=0',
                            ],
                            'addattr': [
                                ('ipaallowedtoperform;read_keys='
                                 'cn=editors,cn=groups,'
                                 'cn=accounts,dc=example,dc=com'),
                                ('ipaallowedtoperform;read_keys='
                                 'cn=hg2,cn=hostgroups,'
                                 'cn=accounts,dc=example,dc=com'),
                                ('managedby='
                                 'fqdn=host2.example.com,cn=computers,'
                                 'cn=accounts,dc=example,dc=com'),
                            ],
                            'delattr': [
                                'certificate=%s' % self.cert,
                                ('ipaallowedtoperform;write_keys='
                                 'fqdn=host2.example.com,cn=computers,'
                                 'cn=accounts,dc=example,dc=com'),
                                ('ipaallowedtoperform;write_keys='
                                 'fqdn=host3.example.com,cn=computers,'
                                 'cn=accounts,dc=example,dc=com'),
                                ('managedby='
                                 'fqdn=host1.example.com,cn=computers,'
                                 'cn=accounts,dc=example,dc=com'),
                            ],
                            'all': True},
                        'method': 'service_mod',
                        'name': [ 'test/host1.example.com@EXAMPLE.COM' ]
                    },
                    reply_updates = {
                        'certificate': None,
                        'ipaallowedtoperform;read_keys': [
                            ( 'cn=editors,cn=groups,'
                              'cn=accounts,dc=example,dc=com'),
                            ( 'cn=hg1,cn=hostgroups,'
                              'cn=accounts,dc=example,dc=com'),
                            ( 'cn=hg2,cn=hostgroups,'
                              'cn=accounts,dc=example,dc=com')],
                        'ipaallowedtoperform;write_keys': [
                            ( 'uid=admin,cn=users,'
                              'cn=accounts,dc=example,dc=com')],
                        'krbticketflags' : [ 0 ],
                        'managedby' : [
                            ( 'fqdn=host2.example.com,cn=computers,'
                              'cn=accounts,dc=example,dc=com')],
                    },
                ),
                # No enable/disable operation
            ],
        )

    def test_19_service_existing_absent(self):
        self.runner(
            test_key = 19,
            module_params = dict(
                krbcanonicalname = "test/host1.example.com@EXAMPLE.COM",
                state = "absent",                     # Absent whole object
                ipa_host = "host1.example.com",
                ipa_user = "admin",
                ipa_pass = "secretpass",
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
                        'name': [ 'test/host1.example.com@EXAMPLE.COM' ]
                    },
                    reply = {},
                ),
                # No enable/disable operation
            ],
        )


