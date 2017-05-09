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
        name=[],
        item=dict(all = True,
                  cn = 'Test ACL' ),
    )

    def test_10_ca_present_new(self):
        self.runner(
            test_key = 10,
            module_params = dict(
                cn = "Test ACL",
                description = "ACL for Ansible testing",
                user = [ 'admin' ],
                group = [ 'editors','admins' ],
                certprofile = 'IECUserRoles',
                ca = ['ipa'],
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
                        'item': {'description': 'ACL for Ansible testing',
                                 'all': True},
                        'method': 'caacl_add',
                        'name': ['Test ACL']},
                    reply_updates = {
                        "description": [ "ACL for Ansible testing" ],
                    },
                ),
                dict(
                    name = 'add user',
                    request = {
                        'method': 'caacl_add_user',
                        'item': {'group': ['admins','editors'],
                                 'user': ['admin'],
                                 'all': True},
                        'name': ['Test ACL']},
                    reply_updates = {
                        'group': ['admins','editors'],
                        'user': ['admin'],
                    },
                ),
                dict(
                    name = 'add certprofile',
                    request = {
                        'method': 'caacl_add_profile',
                        'item': {'certprofile': ['IECUserRoles'],
                                 'all': True},
                        'name': ['Test ACL']},
                    reply_updates = {
                        'certprofile': ['IECUserRoles'],
                    },
                ),
                dict(
                    name = 'add CA',
                    request = {
                        'method': 'caacl_add_ca',
                        'item': {'ca': ['ipa'],
                                 'all': True},
                        'name': ['Test ACL']},
                    reply_updates = {
                        'ca': ['ipa'],
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
                group = [ 'ipausers', 'editors' ], # One redundant, one new
                certprofile = ['caIPAserviceCert'], # New
                state = "present",
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'add user',
                    request = {
                        'method': 'caacl_add_user',
                        'item': {'group': ['ipausers'],
                                 'all': True},
                        'name': ['Test ACL']},
                    reply_updates = {
                        'group': ['admins','editors','ipausers'],
                    },
                ),
                dict(
                    name = 'add certprofile',
                    request = {
                        'method': 'caacl_add_profile',
                        'item': {'certprofile': ['caIPAserviceCert'],
                                 'all': True},
                        'name': ['Test ACL']},
                    reply_updates = {
                        'certprofile': ['IECUserRoles','caIPAserviceCert'],
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
                group = [ 'admins', 'bogus' ], # admins exists, bogus not
                user = ['admin'],              # exists
                host = ['bogushost'],          # not
                state = "absent",
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'remove user/group',
                    request = {
                        'method': 'caacl_remove_user',
                        'item': {'user': ['admin'],
                                 'group': ['admins'],
                                 'all': True},
                        'name': ['Test ACL']},
                    reply_updates = {
                        'user': None,
                        'group': ['editors','ipausers'],
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
                state = "disabled",                 # Disabled; present:
                description = "New description",    # New description
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
                        'item': {'description': 'New description',
                                 'all': True,
                             },
                        'method': 'caacl_mod',
                    },
                    reply_updates = {
                        'description' : ["New description"],
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
                state = "exact",                    # Exact:
                description = "New description",    # Same
                certprofile = 'IECUserRoles',       # Same
                #             'caIPAserviceCert',   # Remove
                # ca = 'ipa',                       # Remove
                group = [
                    # 'ipausers'                    # Remove
                    'editors',                      # Same
                    'trust admins'],                # Add
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                # No modify existing object; desc unchanged
                dict(
                    name = 'add user/group',
                    request = {
                        'method': 'caacl_add_user',
                        'item': {'group': ['trust admins'],
                                 'all': True},
                        'name': ['Test ACL']},
                    reply_updates = {
                        'group': ['editors','ipausers', 'trust admins'],
                    },
                ),
                dict(
                    name = 'remove user/group',
                    request = {
                        'method': 'caacl_remove_user',
                        'item': {'group': ['ipausers'],
                                 'all': True},
                        'name': ['Test ACL']},
                    reply_updates = {
                        'group': ['editors','trust admins'],
                    },
                ),
                dict(
                    name = 'remove certprofile',
                    request = {
                        'method': 'caacl_remove_profile',
                        'item': {'certprofile': ['caIPAserviceCert'],
                                 'all': True},
                        'name': ['Test ACL']},
                    reply_updates = {
                        'certprofile': ['IECUserRoles'],
                    },
                ),
                dict(
                    name = 'remove CA',
                    request = {
                        'method': 'caacl_remove_ca',
                        'item': {'ca': ['ipa'],
                                 'all': True},
                        'name': ['Test ACL']},
                    reply_updates = {
                        'ca': None,
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
            test_key = 16,
            module_params = dict(
                cn = "Test ACL",
                state = "absent",
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
