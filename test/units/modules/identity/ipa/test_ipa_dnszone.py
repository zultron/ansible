# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from . import AbstractEnablableTestClass

from ansible.modules.identity.ipa.ipa_dnszone import DNSZoneIPAClient

import os

class TestDNSZoneIPAClient(unittest.TestCase, AbstractEnablableTestClass):

    test_class = DNSZoneIPAClient

    # Track state from test to test
    current_state = {}

    @property
    def find_request(self):
        return dict(
            method='dnszone_find',
            name=[],
            item=dict(all = True,
                      idnsname = 'test.%s' % self.ipa_domain ),
        )

    def test_10_dnszone_enabled_new(self):
        if self.live_host:
            nsrecord = os.getenv('IPA_NSRECORD', None)
            if nsrecord is None:
                raise RuntimeError(
                    "IPA_NSRECORD environment variable must be set"
                    " in live host mode; e.g. 'host1.example.com.'")
            self.nsrecord = nsrecord.split(',')
        else:
            self.nsrecord = ['host2.%s' % self.ipa_domain]

        self.runner(
            test_key = 10,
            module_params = dict(
                idnsname = "test.%s" % self.ipa_domain,
                state = "enabled",                    # Enabled:
                idnsallowdynupdate = True,            # Add
                idnsallowtransfer = "none;",          # Add
                nsrecord = self.nsrecord,             # Add
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
                        'item' : {'idnsallowtransfer': 'none;',
                                  'idnsallowdynupdate': True,
                                  'addattr': ['nsrecord=%s' % r
                                              for r in self.nsrecord],
                                  'all': True},
                        'method' : 'dnszone_add',
                        'name' : ['test.%s' % self.ipa_domain]},
                    reply_updates = {
                        'idnsallowdynupdate': ['True'],
                        'idnsallowtransfer': ['none;'],
                        'nsrecord': self.nsrecord,
                        'idnszoneactive': [u'TRUE']},
                ),
                # No enable call, since zones are created enabled
            ],
        )

    def test_11_dnszone_existing_present_attr(self):
        self.runner(
            test_key = 11,
            module_params = dict(
                idnsname = "test.%s" % self.ipa_domain,
                state = "enabled",                  # Enabled:
                idnsallowdynupdate = False,         # Modify
                idnsallowtransfer = "none;",        # Noop
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'item' : {'idnsallowdynupdate': False,
                                  'all': True},
                        'method' : 'dnszone_mod',
                        'name' : ['test.%s' % self.ipa_domain]},
                    reply_updates = {
                        'idnsallowdynupdate': ['FALSE'],
                    },
                ),
                # No enable/disable operation
            ],
        )

    def test_12_dnszone_disabled_existing(self):
        self.runner(
            test_key = 12,
            module_params = dict(
                idnsname = "test.%s" % self.ipa_domain,
                state = "disabled",                  # Disabled
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'disable existing object',
                    request = {
                        'item' : {},
                        'method' : 'dnszone_disable',
                        'name' : ['test.%s' % self.ipa_domain]},
                    reply_updates = { 'idnszoneactive': ['FALSE'] },
                ),
            ],
        )

    def test_13_dnszone_remove_existing(self):
        self.runner(
            test_key = 13,
            module_params = dict(
                idnsname = "test.%s" % self.ipa_domain,
                state = "absent",                  # Absent
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'disable existing object',
                    request = {
                        'item' : {},
                        'method' : 'dnszone_del',
                        'name' : ['test.%s' % self.ipa_domain]},
                    reply = {},
                ),
            ],
        )

