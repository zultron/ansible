# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import call, create_autospec, patch
from . import AbstractTestClass

from ansible.modules.identity.ipa.ipa_caacl import CAACLIPAClient

class TestCAACLIPAClient(unittest.TestCase, AbstractTestClass):

    test_class = CAACLIPAClient

    module_params = dict(
        cn = "Test ACL",
        description = "ACL for Ansible testing",
        user = [ 'user1', 'user2' ],
        group = [ 'group1' ],
        # skip hostgroup
        # skip service
        certprofile = 'prof1',
        ca = ['ca1'],
        state = "present",
        ipa_host = "host1.example.com",
        ipa_user = "admin",
        ipa_pass = "secretpass",
    )

    found_obj = {
        "cn" : [ "Test ACL" ],
        "dn" : "ipaUniqueID=6d986c80-6a08,cn=caacls,cn=ca,dc=example,dc=com", 
        "host" : [ 'host1', 'host2', 'host3'],
        "ipaUniqueID": [ "6d986c80-6a08" ], 
        "ipaenabledflag": [ "TRUE" ], 
        "ipamemberca": [ "cn=ipa,cn=cas,cn=ca,dc=example,dc=com" ], 
        "objectClass": [ "ipaassociation", "ipacaacl" ],
    }

    find_params = dict(
        method='caacl_find',
        name=[None],
        item=dict(all = True,
                  cn = 'Test ACL' ),
        item_filter=None,
    )

    # This object makes most operations idempotent; reuse it
    idempotent_obj_updates = {
        'description': ['ACL for Ansible testing'],
        'ca' : ['ca1'],
        'certprofile' : ['prof1'],
        'group' : ['group1'],
        'user' : ['user1', 'user2'],
        'ipaenabledflag' : 'TRUE',
    }

    present_existing_data = {
        'state' : 'present',
        # Object already exists
        'found_obj' : found_obj,
        # Verify dnszone_mod API params
        'aom_params' : {
            'item': {'addattr': ['ca=ca1',
                                 'certprofile=prof1',
                                 'group=group1',
                                 'user=user1',
                                 'user=user2'],
                     'all': True,
                     'delattr': [],
                     'setattr': ['description=ACL for Ansible testing']},
            'item_filter': None,
            'method': 'caacl_mod',
            'name': ['Test ACL']},
        # Idempotency changes
        'idempotent_obj_updates' : idempotent_obj_updates,
    }


    enabled_existing_data = {
        # Object already exists
        'found_obj' : found_obj,
        # Request object state exactly as specified in module params
        'module_params_updates' : {'state' : 'enabled'},
        # Verify dnszone_mod API params
        'aom_params' : {
            'item': {'addattr': ['ca=ca1',
                                 'certprofile=prof1',
                                 'group=group1',
                                 'user=user1',
                                 'user=user2'],
                     'all': True,
                     'delattr': [],
                     'setattr': ['description=ACL for Ansible testing']},
            'item_filter': None,
            'method': 'caacl_mod',
            'name': ['Test ACL']},
        # Idempotency changes
        'idempotent_obj_updates' : idempotent_obj_updates,
    }

    present_new_data = {
        # Object doesn't exist yet
        'found_obj' : {},
        # Verify dnszone_mod API params
        'aom_params' : {
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
        # Idempotency changes
        'idempotent_obj_updates' : idempotent_obj_updates,
    }

    disabled_new_data = {
        # Object doesn't exist yet
        'found_obj' : {},
        # Request object state exactly as specified in module params
        'module_params_updates' : {'state' : 'disabled'},
        # Verify dnszone_mod API params
        'aom_params' : {
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
        # Idempotency changes
        'idempotent_obj_updates' : {
            'description': ['ACL for Ansible testing'],
            'ca' : ['ca1'],
            'certprofile' : ['prof1'],
            'group' : ['group1'],
            'host' : ['host1', 'host2', 'host3'],
            'user' : ['user1', 'user2'],
            'ipaenabledflag' : ['FALSE'],
        },
    }

    exact_existing_data = {
        # Object already exists
        'found_obj' : found_obj,
        # Request object state exactly as specified in module params
        'module_params_updates' : {'state' : 'exact'},
        # Verify dnszone_mod API params
        'aom_params' : {
            'item': {'addattr': ['ca=ca1',
                                 'certprofile=prof1',
                                 'group=group1',
                                 'user=user1',
                                 'user=user2'],
                     'all': True,
                     'delattr': ['host=host1', 'host=host2', 'host=host3'],
                     'setattr': ['description=ACL for Ansible testing']},
            'item_filter': None,
            'method': 'caacl_mod',
            'name': ['Test ACL']},
        # Idempotency changes
        'idempotent_obj_updates' : {
            'description': ['ACL for Ansible testing'],
            'ca' : ['ca1'],
            'certprofile' : ['prof1'],
            'group' : ['group1'],
            'user' : ['user1', 'user2'],
            'host' : [None],
        },
    }

    rem_params = {
        'item': {},
        'item_filter': None,
        'method': 'caacl_del',
        'name': ['Test ACL']}
