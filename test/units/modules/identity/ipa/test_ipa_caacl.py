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
    )

    def test_10_ca_present_new(self):
        self.runner(
            test_key = 10,
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

    def test_11_ca_existing_present_listattr(self):
        self.runner(
            test_key = 11,
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
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'item': {'addattr': ['certprofile=prof2',
                                             'user=user3'],
                                 'all': True,
                                 'delattr': [],
                                 'setattr': []},
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

    def test_12_ca_existing_absent_listattr(self):
        self.runner(
            test_key = 12,
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
                ),
                dict(
                    name = 'modify existing object',
                    request = {
                        'item': {'addattr': [],
                                 'all': True,
                                 'delattr': ['group=group1',
                                             'user=user3'],
                                 'setattr': []},
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

    def test_13_ca_existing_disable_strattr(self):
        self.runner(
            test_key = 13,
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
                        'item': {},
                    },
                    reply_updates = {
                        "ipaenabledflag": [ "FALSE" ], 
                    },
                ),
            ],
        )

    def test_14_ca_existing_exact(self):
        self.runner(
            test_key = 14,
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

    def test_15_ca_existing_enable(self):
        self.runner(
            test_key = 15,
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
                ),
                # No modification call to existing object
                dict(
                    name = 'enable existing object',
                    request = {
                        'name': ['Test ACL'],
                        'method': 'caacl_enable',
                        'item': {},
                    },
                    reply_updates = {
                        "ipaenabledflag": [ "TRUE" ], 
                    },
                ),
            ],
        )

    def test_16_ca_existing_rem(self):
        self.runner(
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
                ),
                # No modification call to existing object
                dict(
                    name = 'remove existing object',
                    request = {
                        'item': {},
                        'method': 'caacl_del',
                        'name': ['Test ACL']},
                    reply = {},
                ),
            ],
        )
