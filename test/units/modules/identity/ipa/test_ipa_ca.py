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
        'item_filter': None,
    }

    def test_10_ca_present_new(self):
        client = self.runner(
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
                    reply = {
                        "cn": [ "Test CA" ],
                        "dn": "cn=Test CA,cn=cas,cn=ca,dc=example,dc=com",
                        "ipacaid": [ "a668e97e-2015-415d-a353-c25297950516" ], 
                        "ipacaissuerdn": [ "CN=Certificate Authority,O=EXAMPLE.COM" ],
                        "ipacasubjectdn": [ "CN=Test CA,O=EXAMPLE.COM" ],
                    },
                ),
                dict(
                    name = 'add new object',
                    request = {
                        'name' : ['Test CA'],
                        'item' : {'all': True,
                                  'setattr': ['description=For testing Ansible'],
                                  'addattr': [],
                                  'delattr': []},
                        'method' : 'ca_mod',
                        'item_filter': None,
                    },
                    reply_updates = {
                        "description": [ "For testing Ansible" ]},
                ),
                # no enable_or_disable
            ],
        )

        # Persist client between tests
        self.current_state['client10'] = client


    def test_11_ca_delattr_existing(self):
        client = self.runner(
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
                    reply = self.current_state['client10'].final_obj,
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
                        'item_filter': None,
                    },
                    # recycle reply; not needed
                    reply_updates = {
                        "description": [ None ]},
                ),
            ],
        )

        # Persist client between tests
        self.current_state['client11'] = client

    def test_12_ca_exact_existing(self):
        client = self.runner(
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
                    reply = self.current_state['client11'].final_obj,
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
                        'item_filter': None,
                    },
                    reply_updates = {
                        "description": [ "Some Ansible test artifact" ]},
                ),
            ],
        )

        # Persist client between tests
        self.current_state['client12'] = client

    def test_13_ca_absent_existing(self):
        client = self.runner(
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
                    reply = self.current_state['client12'].final_obj,
                ),
                # rem()
                dict(
                    name = 'absent/del existing object',
                    request = {
                        'name' : [ "Test CA" ],
                        'item' : {},
                        "method": "ca_del",
                        'item_filter' : None,
                    },
                    reply = {},
                ),
            ],
        )

        # Persist client between tests
        self.current_state['client13'] = client
