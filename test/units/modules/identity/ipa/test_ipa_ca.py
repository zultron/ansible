# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import call, create_autospec, patch
from . import AbstractTestClass

from ansible.modules.identity.ipa.ipa_ca import CAIPAClient

class TestCAIPAClient(unittest.TestCase, AbstractTestClass):

    test_class = CAIPAClient

    module_params = dict(
        cn = "Test CA",
        description = "For testing Ansible",
        state = "present",
        ipa_host = "host1.example.com",
        ipa_user = "admin",
        ipa_pass = "secretpass",
    )

    found_obj =  {
        "cn": [ "Test CA" ],
        "dn": "cn=Test CA,cn=cas,cn=ca,dc=example,dc=com",
        "ipacaid": [ "a668e97e-2015-415d-a353-c25297950516" ], 
        "ipacaissuerdn": [ "CN=Certificate Authority,O=EXAMPLE.COM" ],
        "ipacasubjectdn": [ "CN=Test CA,O=EXAMPLE.COM" ],
    }

    find_params =  {
        'item': {'all': True, 'cn': 'Test CA'},
        'method': 'ca_find',
        'name': [None],
        'item_filter': None,
    }


    # These changes make most operations idempotent
    idempotent_obj_updates = {
        "description": [ "For testing Ansible" ]}

    present_existing_data = {
        # Object already exists
        'found_obj' : found_obj,
        # Verify ca_mod API params
        'aom_params' : {
            'name' : ['Test CA'],
            'item' : {'all': True,
                      'setattr': ['description=For testing Ansible'],
                      'addattr': [],
                      'delattr': []},
            'method' : 'ca_mod',
            'item_filter': None},
        # Idempotency changes
        'idempotent_obj_updates' : idempotent_obj_updates,
    }

    enabled_existing_data = 'N/A (en/disable unsupported)'

    present_new_data = {
        # Object doesn't yet exist
        'found_obj' : {},
        # Verify ca_add API params
        'aom_params' : {
            'name' : ['Test CA'],
            'item' : {'all': True,
                      'setattr': ['description=For testing Ansible'],
                      'addattr': [],
                      'delattr': []},
            'method' : 'ca_add',
            'item_filter': None},
        # Idempotency
        'idempotent_obj' : found_obj,
        'idempotent_obj_updates' : idempotent_obj_updates,
    }

    disabled_new_data = 'N/A (en/disable unsupported)'

    exact_existing_data = {
        # Object already exists; try deleting description
        'found_obj' : found_obj,
        'found_obj_updates' : { 'description' : 'To be deleted' },
        # Request object state exactly as specified in module params
        'module_params_updates' : {
            'state' : 'exact',
            'description' : None},
        # Verify ca_mod API params
        'aom_params' : {
            'name' : ['Test CA'],
            'item' : {'all': True,
                      'setattr': [],
                      'addattr': [],
                      'delattr': ['description=To be deleted']},
            'method' : 'ca_mod',
            'item_filter': None},
        # Idempotency
        'idempotent_obj' : found_obj,
    }

    rem_params = {
        'name' : [ "Test CA" ],
        'item' : {},
        "method": "ca_del",
        'item_filter' : None,
    }
