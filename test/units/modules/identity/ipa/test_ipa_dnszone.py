# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from . import AbstractTestClass

from ansible.modules.identity.ipa.ipa_dnszone import DNSZoneIPAClient

class TestDNSZoneIPAClient(unittest.TestCase, AbstractTestClass):

    test_class = DNSZoneIPAClient

    # Track state from test to test
    current_state = {}

    find_request = dict(
        method='dnszone_find',
        name=[None],
        item=dict(all = True,
                  idnsname = 'test.example.com' ),
        item_filter=None,
    )

    def test_10_dnszone_enabled_new(self):
        test = 10
        # Create new object
        client = self.runner(
            module_params = dict(
                idnsname = "test.example.com",
                state = "enabled",                  # Enabled:
                idnsallowdynupdate = True,          # Add
                idnsallowtransfer = "none;",        # Add
                nsrecord = "host2.example.com.",    # Add
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
                        'item' : {'setattr': ['idnsallowdynupdate=True',
                                              'idnsallowtransfer=none;',
                                              'nsrecord=host2.example.com.'],
                                  'delattr': [], 'addattr': [], 'all': True},
                        'item_filter': None,
                        'method' : 'dnszone_add',
                        'name' : ['test.example.com']},
                    reply_updates = {
                        'idnsallowdynupdate': ['True'],
                        'idnsallowtransfer': ['none;'],
                        'nsrecord': ['host2.example.com.']},
                ),
                dict(
                    name = 'enable new object',
                    request = {
                        'item' : {},
                        'item_filter': None,
                        'method' : 'dnszone_enable',
                        'name' : ['test.example.com']},
                    reply_updates = { 'idnszoneactive': ['TRUE'] },
                ),
            ],
        )

        # Persist client between tests
        self.current_state['client%d' % test] = client

    def test_11_dnszone_existing_present_attr(self):
        test = 11
        client = self.runner(
            module_params = dict(
                idnsname = "test.example.com",
                state = "enabled",                  # Enabled:
                idnsallowdynupdate = False,         # Modify
                idnsallowtransfer = "none;",        # Noop
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
                        'item' : {'setattr': ['idnsallowdynupdate=False' ],
                                  'addattr': [], 'delattr': [], 'all': True},
                        'item_filter': None,
                        'method' : 'dnszone_mod',
                        'name' : ['test.example.com']},
                    reply_updates = {
                        'idnsallowdynupdate': ['FALSE'],
                    },
                ),
                # No enable/disable operation
            ],
        )

        # Persist client between tests
        self.current_state['client%d' % test] = client

    def test_12_dnszone_disabled_existing(self):
        test = 12
        # Disable object w/no other changes
        client = self.runner(
            module_params = dict(
                idnsname = "test.example.com",
                state = "disabled",                  # Disabled
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
                    name = 'disable existing object',
                    request = {
                        'item' : {},
                        'item_filter': None,
                        'method' : 'dnszone_disable',
                        'name' : ['test.example.com']},
                    reply_updates = { 'idnszoneactive': ['FALSE'] },
                ),
            ],
        )

        # Persist client between tests
        self.current_state['client%d' % test] = client

    def test_13_dnszone_remove_existing(self):
        test = 13
        # Remove object
        client = self.runner(
            module_params = dict(
                idnsname = "test.example.com",
                state = "absent",                  # Absent
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
                    name = 'disable existing object',
                    request = {
                        'item' : {},
                        'method' : 'dnszone_del',
                        'name' : ['test.example.com'],
                        'item_filter' : None},
                    reply = {},
                ),
            ],
        )

        # Persist client between tests
        self.current_state['client%d' % test] = client

