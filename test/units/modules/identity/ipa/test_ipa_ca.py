# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from . import AbstractTestClass

from ansible.modules.identity.ipa.ipa_ca import CAIPAClient

class TestCAIPAClient(unittest.TestCase, AbstractTestClass):

    test_class = CAIPAClient

    # Track state from test to test
    current_state = {}

    find_request = {
        'item': {'all': True, 'cn': 'Test CA'},
        'method': 'ca_find',
        'name': [None],
    }

    def test_10_ca_present_new(self):
        self.runner(
            test_key = 10,
            module_params = dict(
                cn = "Test CA",
                description = "For testing Ansible",
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
                        'name' : ['Test CA'],
                        'item' : {'all': True,
                                  'setattr': ['description=For testing Ansible'],
                                  'addattr': [],
                                  'delattr': []},
                        'method' : 'ca_add',
                    },
                    reply_updates = {
                        "description": [ "For testing Ansible" ]},
                ),
                # no enable_or_disable
            ],
        )


    def test_11_ca_delattr_existing(self):
        self.runner(
            test_key = 11,
            module_params = dict(
                cn = "Test CA",
                state = "absent",
                description = "For testing Ansible",
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
                    name = 'absent/modify existing object',
                    request = {
                        'name' : ['Test CA'],
                        'item' : {'all': True,
                                  'setattr': [],
                                  'addattr': [],
                                  'delattr': ['description=For testing Ansible']},
                        'method' : 'ca_mod',
                    },
                    # recycle reply; not needed
                    reply_updates = {
                        "description": [ None ]},
                ),
            ],
        )

    def test_12_ca_exact_existing(self):
        self.runner(
            test_key = 12,
            module_params = dict(
                cn = "Test CA",
                state = "exact",
                description = "Some Ansible test artifact",
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
                    name = 'exact/modify existing object',
                    request = {
                        'name' : ['Test CA'],
                        'item' : {'all': True,
                                  'setattr': [
                                      'description=Some Ansible test artifact'],
                                  'addattr': [],
                                  'delattr': []},
                        'method' : 'ca_mod',
                    },
                    reply_updates = {
                        "description": [ "Some Ansible test artifact" ]},
                ),
            ],
        )

    def test_13_ca_absent_existing(self):
        self.runner(
            test_key = 13,
            module_params = dict(
                cn = "Test CA",
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
                # rem()
                dict(
                    name = 'absent/del existing object',
                    request = {
                        'name' : [ "Test CA" ],
                        'item' : {},
                        "method": "ca_del",
                    },
                    reply = {},
                ),
            ],
        )
