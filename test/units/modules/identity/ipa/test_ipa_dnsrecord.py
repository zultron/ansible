# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import call, create_autospec, patch
from . import AbstractTestClass

from ansible.modules.identity.ipa.ipa_dnsrecord import DNSRecordIPAClient

class TestDNSRecordIPAClient(unittest.TestCase, AbstractTestClass):

    test_class = DNSRecordIPAClient

    # Track state from test to test
    current_state = {}

    find_request = dict(
        method='dnsrecord_find',
        name=['example.com'],
        item=dict(all = True,
                  idnsname = {'__dns_name__':'host1'} ),
        item_filter=None,
    )

    def test_10_dnsrecord_present_new(self):
        test = 10
        # Create new object
        client = self.runner(
            module_params = dict(
                zone = "example.com",
                idnsname = "host1",
                arecord = [ "192.168.42.38", "192.168.43.38" ],
                txtrecord = "new text",
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
                        'item': {'addattr': ['arecord=192.168.42.38',
                                             'arecord=192.168.43.38',
                                             'txtrecord=new text'],
                                 'all': True,
                                 'delattr': [],
                                 'setattr': []},
                        'item_filter': None,
                        'method': 'dnsrecord_add',
                        'name': ['example.com', {'__dns_name__': 'host1'}]},
                    reply_updates = {
                        'arecord': ['192.168.42.38', '192.168.43.38'],
                        'txtrecord': ['new text']},
                ),
                # No enable/disable operation
            ],
        )

        # Persist client between tests
        self.current_state['client%d' % test] = client

    def test_11_dnsrecord_existing_present_listattr(self):
        test = 11
        client = self.runner(
            module_params = dict(
                zone = "example.com",
                idnsname = "host1",
                state = "present",                 # Present:
                arecord = [ "192.168.42.39" ],     # New
                mxrecord = ['10 mx1.example.com',  # New
                            '10 mx2.example.com',  # New
                            '10 mx3.example.com'], # New
                txtrecord = "new text",            # Same
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
                        'name': ['example.com', {'__dns_name__': 'host1'}],
                        'item': {'addattr': ['arecord=192.168.42.39',
                                             'mxrecord=10 mx1.example.com',
                                             'mxrecord=10 mx2.example.com',
                                             'mxrecord=10 mx3.example.com' ],
                                 'all': True, 'delattr': [], 'setattr': []},
                        'method': 'dnsrecord_mod',
                        'item_filter': None,
                    },
                    reply_updates = {
                        'arecord': [ "192.168.42.38",
                                     "192.168.43.38",
                                     "192.168.42.39" ],
                        'mxrecord': ['10 mx1.example.com',
                                     '10 mx2.example.com',
                                     '10 mx3.example.com' ],
                    },
                ),
                # No enable/disable operation
            ],
        )

        # Persist client between tests
        self.current_state['client%d' % test] = client

    def test_12_ca_existing_absent_listattr(self):
        test = 12
        client = self.runner(
            module_params = dict(
                zone = "example.com",
                idnsname = "host1",
                state = "absent",                            # Absent:
                arecord = [ "192.168.42.38",                 # Remove
                            "192.168.43.38",                 # Remove
                            "192.168.42.50" ],               # Noop
                srvrecord = [ '0 100 88 h01.zultron.com.' ], # Noop
                mxrecord = ['10 mx2.example.com',            # Remove
                            '10 mx3.example.com'],           # Remove
                txtrecord = "new text",                      # Remove
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
                    name = 'delete attributes from existing object',
                    request = {
                        'item': {'delattr': ['arecord=192.168.42.38',
                                             'arecord=192.168.43.38',
                                             'mxrecord=10 mx2.example.com',
                                             'mxrecord=10 mx3.example.com',
                                             'txtrecord=new text' ],
                                 'addattr': [], 'setattr': [], 'all': True},
                        'item_filter': None,
                        'method': 'dnsrecord_mod',
                        'name': ['example.com', {'__dns_name__': 'host1'}]},
                    reply_updates = {
                        'arecord': [ "192.168.42.39" ],
                        'mxrecord': ['10 mx1.example.com' ],
                        'txtrecord': None,
                    },
                ),
                # No enable/disable operation
            ],
        )

        # Persist client between tests
        self.current_state['client%d' % test] = client

    def test_13_dnsrecord_existing_exact(self):
        test = 13
        client = self.runner(
            module_params = dict(
                zone = "example.com",
                idnsname = "host1",
                state = "exact",                                 # Exact:
                arecord = [ "192.168.42.39",                     # Noop
                            "192.168.42.38" ],                   # Add
                mxrecord = [# '10 mx1.example.com',              # Remove
                            '10 mx2.example.com' ],              # Add
                txtrecord = "newer text",                        # Add
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
                    name = 'exact modify existing object',
                    request = {
                        'item': {
                            'addattr': [
                                'arecord=192.168.42.38',
                                'mxrecord=10 mx2.example.com',
                                'txtrecord=newer text',                            
                            ],
                            'delattr': [
                                'mxrecord=10 mx1.example.com' ],
                            'setattr': [], 'all': True},
                        'method': 'dnsrecord_mod',
                        'item_filter': None,
                        'name': ['example.com', {'__dns_name__': 'host1'}]},
                    reply_updates = {
                        'arecord': [ "192.168.42.39", "192.168.42.38" ],
                        'mxrecord': [ '10 mx2.example.com' ],
                        'txtrecord': [ 'newer text' ],
                    },
                ),
                # No enable/disable operation
            ],
        )

        # Persist client between tests
        self.current_state['client%d' % test] = client

    def test_14_dnsrecord_existing_absent_object(self):
        test = 14
        client = self.runner(
            module_params = dict(
                zone = "example.com",
                idnsname = "host1",
                state = "absent",                         # Absent
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
                    name = 'remove existing object',
                    request = {
                        'item': {},
                        'item_filter': None,
                        'method': 'dnsrecord_del',
                        'name': ['example.com', {'__dns_name__': 'host1'}]},
                    reply = {},
                ),
                # No enable/disable operation
            ],
        )

        # Persist client between tests
        self.current_state['client%d' % test] = client
