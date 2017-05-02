# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from . import AbstractTestClass

from ansible.modules.identity.ipa.ipa_caacl import CAACLIPAClient

class TestCAACLIPAClient(unittest.TestCase, AbstractTestClass):

    test_class = CAACLIPAClient

    # Track state from test to test
    current_state = {}

    find_request = dict(
        method='caacl_find',
        name=[None],
        item=dict(all = True,
                  cn = 'Test ACL' ),
        item_filter=None,
    )

    def test_10_ca_present_new(self):
        test = 10
        # Create new object
        client = self.runner(
            module_params = dict(
                cn = "Test ACL",
                description = "ACL for Ansible testing",
                user = [ 'user1', 'user2' ],
                group = [ 'group1' ],
                certprofile = 'prof1',
                ca = ['ca1'],
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
                        'item': {'addattr': ['ca=ca1',
                                             'certprofile=prof1',
                                             'group=group1',
                                             'user=user1',
                                             'user=user2'],
                                 'all': True,
                                 'delattr': [],
                                 'setattr': ['description=ACL for Ansible testing']},
                        'item_filter': None,
                        'method': 'caacl_add',
                        'name': ['Test ACL']},
                    reply_updates = {
                        "description": [ "ACL for Ansible testing" ],
                        'ca': ['ca1'],
                        'certprofile': ['prof1'],
                        'group': ['group1'],
                        'user': ['user1', 'user2'],
                    },
                ),
                # No enable/disable operation
            ],
        )

        # Persist client between tests
        self.current_state['client%d' % test] = client

    def test_11_ca_existing_present_listattr(self):
        test = 11
        client = self.runner(
            module_params = dict(
                cn = "Test ACL",
                user = [ 'user1', 'user3' ], # One redundant, one new
                certprofile = ['prof2'], # New
                state = "present",
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
                        'item': {'addattr': ['certprofile=prof2',
                                             'user=user3'],
                                 'all': True,
                                 'delattr': [],
                                 'setattr': []},
                        'item_filter': None,
                        'method': 'caacl_mod',
                        'name': ['Test ACL']},
                    reply_updates = {
                        'user': ['user1', 'user3'],
                        'certprofile': ['prof2'],
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
                cn = "Test ACL",
                user = [ 'user3', 'user4' ], # user3 exists, user4 not
                group = ['group1'], # exists
                host = ['host1'], # not
                state = "absent",
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
                        'item': {'addattr': [],
                                 'all': True,
                                 'delattr': ['group=group1',
                                             'user=user3'],
                                 'setattr': []},
                        'item_filter': None,
                        'method': 'caacl_mod',
                        'name': ['Test ACL']},
                    reply_updates = {
                        'user': None,
                        'group': None,
                    },
                ),
                # No enable/disable operation
            ],
        )

        # Persist client between tests
        self.current_state['client%d' % test] = client


    def test_13_ca_existing_disable_strattr(self):
        test = 13
        client = self.runner(
            module_params = dict(
                cn = "Test ACL",
                state = "disabled",               # Disabled; present:
                description = "New description",  # New description
                host = ['host1.example.com',      # Add
                        'host2.example.com'],     # Add
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
                        'name': ['Test ACL'],
                        'item': {'addattr': ['host=host1.example.com',
                                             'host=host2.example.com'],
                                 'setattr': ['description=New description'],
                                 'delattr': [], 'all': True,
                             },
                        'method': 'caacl_mod',
                        'item_filter': None,
                    },
                    reply_updates = {
                        'description' : ["New description"],
                        'host': ['host1.example.com',
                                 'host2.example.com'],
                        "ipaenabledflag": [ "TRUE" ], 
                    },
                ),
                dict(
                    name = 'disable existing object',
                    request = {
                        'name': ['Test ACL'],
                        'method': 'caacl_disable',
                        'item': {}, 'item_filter': None,
                    },
                    reply_updates = {
                        "ipaenabledflag": [ "FALSE" ], 
                    },
                ),
            ],
        )

        # Persist client between tests
        self.current_state['client%d' % test] = client

    def test_14_ca_existing_exact(self):
        test = 14
        client = self.runner(
            module_params = dict(
                cn = "Test ACL",
                state = "exact",                  # Exact:
                description = "New description",  # Same
                certprofile = 'prof2',            # Same
                # ca                              # Remove
                host = [# host1.example.com       # Remove
                        'host2.example.com',      # Same
                        'host3.example.com'],     # Add
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
                        'name': ['Test ACL'],
                        'item': {'addattr': ['host=host3.example.com'],
                                 'delattr': ['ca=ca1',
                                             'host=host1.example.com'],
                                 'setattr': [], 'all': True},
                        'method': 'caacl_mod',
                        'item_filter': None,
                    },
                    reply_updates = {
                        'host' : ['host2.example.com',
                                  'host3.example.com'],
                        'ca' : None,
                    },
                ),
                # No enable/disable operation
            ],
        )

        # Persist client between tests
        self.current_state['client%d' % test] = client

    def test_15_ca_existing_enable(self):
        test = 15
        client = self.runner(
            module_params = dict(
                cn = "Test ACL",
                state = "enabled",                # Enabled, no other changes
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
                # No modification call to existing object
                dict(
                    name = 'enable existing object',
                    request = {
                        'name': ['Test ACL'],
                        'method': 'caacl_enable',
                        'item': {}, 'item_filter': None,
                    },
                    reply_updates = {
                        "ipaenabledflag": [ "TRUE" ], 
                    },
                ),
            ],
        )

        # Persist client between tests
        self.current_state['client%d' % test] = client

    def test_16_ca_existing_rem(self):
        test = 16
        client = self.runner(
            module_params = dict(
                cn = "Test ACL",
                state = "absent",
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
                # No modification call to existing object
                dict(
                    name = 'remove existing object',
                    request = {
                        'item': {},
                        'item_filter': None,
                        'method': 'caacl_del',
                        'name': ['Test ACL']},
                    reply = {},
                ),
            ],
        )

        # Persist client between tests
        self.current_state['client%d' % test] = client
