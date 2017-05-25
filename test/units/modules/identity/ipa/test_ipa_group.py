# Make coding more python3-ish
__metaclass__ = type

from ansible.compat.tests import unittest
from . import AbstractTestClass

from ansible.modules.identity.ipa.ipa_group import GroupIPAClient

class TestGroupIPAClient(unittest.TestCase, AbstractTestClass):

    test_class = GroupIPAClient

    # Track state from test to test
    current_state = {}

    find_request = dict(
        method='group_find',
        name=[],
        item=dict(
            all = True,
            cn = 'test_group',
        ),
    )

    def test_10_group_present_new(self):
        self.runner(
            test_key = 10,
            module_params = dict(
                cn = 'test_group',
                gidnumber = 12982,
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
                        'item': {'gidnumber': 12982,
                                 'all': True},
                        'method': 'group_add',
                        'name': ['test_group']},
                    reply = {
                        'cn': 'test_group',
                        'gidnumber': 12982,
                    },
                ),
            ],
        )

    def test_11_group_existing_present_attr(self):
        self.runner(
            test_key = 11,
            module_params = dict(
                cn = 'test_group',                       # Key
                description = 'A Test Group',            # Add str
                member_user = 'admin',                   # Add to list
                member_group = [ 'admins', 'editors' ],  # Add to list
                state = "present",
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'add description',
                    request = {
                        'item' : { 'description': 'A Test Group',
                                   'all': True},
                        'method' : 'group_mod',
                        'name' : ['test_group']},
                    reply_updates = {
                        'description': 'A Test Group',
                    },
                ),
                dict(
                    name = 'add user and groups',
                    request = {
                        'item' : { 'group': [
                                       'admins',
                                       'editors',
                                   ],
                                   'user': [
                                       'admin',
                                   ],
                                   'all': True},
                        'method' : 'group_add_member',
                        'name' : ['test_group']},
                    reply_updates = {
                        'member_user': [ 'admin' ],
                        'member_group': [
                            'admins',
                            'editors',
                        ],
                    },
                ),
                # No enable/disable operation
            ],
        )

    def test_12_group_existing_absent_attr(self):
        self.runner(
            test_key = 12,
            module_params = dict(
                cn = 'test_group',                       # Key
                description = 'A Test Group',            # Remove str
                member_group = [ 'admins' ],             # Remove from list
                state = "absent",
            ),
            post_json_calls = [
                dict(
                    name = 'find existing object',
                    request = self.find_request,
                ),
                dict(
                    name = 'delete description',
                    request = {
                        'item' : { 'description': None,
                                   'all': True},
                        'method' : 'group_mod',
                        'name' : ['test_group']},
                    reply_updates = {
                        'description': None,
                    },
                ),
                dict(
                    name = 'delete group',
                    request = {
                        'item' : { 'group': [
                                       'admins',
                                   ],
                                   'all': True},
                        'method' : 'group_remove_member',
                        'name' : ['test_group']},
                    reply_updates = {
                        'description': None,
                        'member_group': [ 'editors' ],
                    },
                ),
                # No enable/disable operation
            ],
        )


    def test_13_group_remove_existing(self):
        self.runner(
            test_key = 13,
            module_params = dict(
                cn = 'test_group',                 # Key
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
                        'method' : 'group_del',
                        'name' : ['test_group']},
                    reply = {},
                ),
            ],
        )

