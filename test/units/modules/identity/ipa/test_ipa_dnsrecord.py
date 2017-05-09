# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from . import AbstractTestClass

from ansible.modules.identity.ipa.ipa_dnsrecord import DNSRecordIPAClient

class TestDNSRecordIPAClient(unittest.TestCase, AbstractTestClass):

    test_class = DNSRecordIPAClient

    # Track state from test to test
    current_state = {}

    @property
    def find_request(self):
        return dict(
            method='dnsrecord_find',
            name=[ self.domain ],
            item={'all': True,
                  'idnsname': {'__dns_name__':'host1'}},
        )

    def test_10_dnsrecord_present_new(self):
        self.runner(
            test_key = 10,
            module_params = dict(
                zone = self.domain,
                idnsname = "host1",
                arecord = [ "192.168.42.38", "192.168.43.38" ],
                txtrecord = "new text",
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
                        'item': {'addattr': ['arecord=192.168.42.38',
                                             'arecord=192.168.43.38',
                                             'txtrecord=new text'],
                                 'all': True},
                        'method': 'dnsrecord_add',
                        'name': [self.domain, {'__dns_name__': 'host1'}]},
                    reply_updates = {
                        'arecord': ['192.168.42.38', '192.168.43.38'],
                        'txtrecord': ['new text']},
                ),
                # No enable/disable operation
            ],
        )

    def test_11_dnsrecord_existing_present_listattr(self):
        self.runner(
            test_key = 11,
            module_params = dict(
                zone = self.domain,
                idnsname = "host1",
                state = "present",                      # Present:
                arecord = [ "192.168.42.39" ],          # New
                mxrecord = ['10 mx1.%s' % self.domain,  # New
                            '10 mx2.%s' % self.domain,  # New
                            '10 mx3.%s' % self.domain], # New
                txtrecord = "new text",                 # Same
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'name': [self.domain, {'__dns_name__': 'host1'}],
                        'item': {'addattr': [
                            'arecord=192.168.42.39',
                            'mxrecord=10 mx1.%s' % self.domain,
                            'mxrecord=10 mx2.%s' % self.domain,
                            'mxrecord=10 mx3.%s' % self.domain ],
                                 'all': True},
                        'method': 'dnsrecord_mod',
                    },
                    reply_updates = {
                        'arecord': [ "192.168.42.38",
                                     "192.168.43.38",
                                     "192.168.42.39" ],
                        'mxrecord': ['10 mx1.%s' % self.domain,
                                     '10 mx2.%s' % self.domain,
                                     '10 mx3.%s' % self.domain ],
                    },
                ),
                # No enable/disable operation
            ],
        )

    def test_12_dnsrecord_existing_absent_listattr(self):
        self.runner(
            test_key = 12,
            module_params = dict(
                zone = self.domain,
                idnsname = "host1",
                state = "absent",                            # Absent:
                arecord = [ "192.168.42.38",                 # Remove
                            "192.168.43.38",                 # Remove
                            "192.168.42.50" ],               # Noop
                srvrecord = [
                    '0 100 88 host1.%s.' % self.domain ],    # Noop
                mxrecord = ['10 mx2.%s' % self.domain,       # Remove
                            '10 mx3.%s' % self.domain],      # Remove
                txtrecord = "new text",                      # Remove
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'delete attributes from existing object',
                    request = {
                        'item': {'delattr': ['arecord=192.168.42.38',
                                             'arecord=192.168.43.38',
                                             'mxrecord=10 mx2.%s' % self.domain,
                                             'mxrecord=10 mx3.%s' % self.domain,
                                             'txtrecord=new text' ],
                                 'all': True},
                        'method': 'dnsrecord_mod',
                        'name': [self.domain, {'__dns_name__': 'host1'}]},
                    reply_updates = {
                        'arecord': [ "192.168.42.39" ],
                        'mxrecord': ['10 mx1.%s' % self.domain ],
                        'txtrecord': None,
                    },
                ),
                # No enable/disable operation
            ],
        )

    def test_13_dnsrecord_existing_exact(self):
        self.runner(
            test_key = 13,
            module_params = dict(
                zone = "%s" % self.domain,
                idnsname = "host1",
                state = "exact",                                 # Exact:
                arecord = [ "192.168.42.39",                     # Noop
                            "192.168.42.38" ],                   # Add
                mxrecord = [# '10 mx1.%s' % self.domain,         # Remove
                            '10 mx2.%s' % self.domain ],         # Add
                txtrecord = "newer text",                        # Add
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'exact modify existing object',
                    request = {
                        'item': {
                            'addattr': [
                                'arecord=192.168.42.38',
                                'mxrecord=10 mx2.%s' % self.domain,
                                'txtrecord=newer text',                            
                            ],
                            'delattr': [
                                'mxrecord=10 mx1.%s' % self.domain ],
                            'all': True},
                        'method': 'dnsrecord_mod',
                        'name': [self.domain, {'__dns_name__': 'host1'}]},
                    reply_updates = {
                        'arecord': [ "192.168.42.39", "192.168.42.38" ],
                        'mxrecord': [ '10 mx2.%s' % self.domain ],
                        'txtrecord': [ 'newer text' ],
                    },
                ),
                # No enable/disable operation
            ],
        )

    def test_14_dnsrecord_existing_absent_object(self):
        self.runner(
            test_key = 14,
            module_params = dict(
                zone = self.domain,
                idnsname = "host1",
                state = "absent",                         # Absent
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'remove existing object',
                    request = {
                        'item': {'del_all' : True},
                        'method': 'dnsrecord_del',
                        'name': ['%s' % self.domain,
                                 {'__dns_name__': 'host1'}]},
                    reply = {},
                ),
                # No enable/disable operation
            ],
        )
