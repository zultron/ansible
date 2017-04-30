# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import call, create_autospec, patch
from . import t_st_ipa_abstract

from ansible.modules.identity.ipa.ipa_dnsrecord import DNSRecordIPAClient

class TestDNSRecordIPAClient(t_st_ipa_abstract.AbstractTestClass):

    test_class = DNSRecordIPAClient

    module_params = dict(
        zone = "example.com",
        idnsname = "host1",
        arecord = [ "192.168.42.38", "192.168.43.38" ],
        txtrecord = "new text",
        state = "present",
        ipa_host = "host1.example.com",
        ipa_user = "admin",
        ipa_pass = "secretpass",
    )

    found_obj = {
        'arecord': ['192.168.42.37', '192.168.43.38'],
        'dn': 'idnsname=host1,idnsname=example.com.,cn=dns,dc=example,dc=com',
        'idnsname': ['host1'],
        'mxrecord': ['10 mx.example.com'],
        'objectClass': ['top', 'idnsrecord'],
        'txtrecord': ['old text', 'old text 2']}

    find_params = dict(
        method='dnsrecord_find',
        name=['example.com'],
        item=dict(all = True,
                  idnsname = {'__dns_name__':'host1'} ),
        item_filter=None,
    )

    # This object makes most operations idempotent; reuse it
    idempotent_obj_updates = {
        'arecord': ['192.168.42.37', '192.168.43.38', '192.168.42.38'],
        'txtrecord': ['old text', 'old text 2', 'new text'],
    }

    present_existing_data = {
        # Object already exists
        'found_obj' : found_obj,
        # Verify dnszone_mod API params
        'aom_params' : {
            'item': {'addattr': ['arecord=192.168.42.38',
                                 'txtrecord=new text'],
                     'all': True,
                     'delattr': [],
                     'setattr': []},
            'item_filter': None,
            'method': 'dnsrecord_mod',
            'name': ['example.com', {'__dns_name__': 'host1'}]},
        # Idempotency changes
        'idempotent_obj_updates' : idempotent_obj_updates,
    }

    enabled_existing_data = 'N/A (en/disable unsupported)'

    present_new_data = {
        # Object doesn't exist yet
        'found_obj' : {},
        # Verify dnsrecord_add API params
        'aom_params' : {
            'item': {'addattr': ['arecord=192.168.42.38',
                                 'arecord=192.168.43.38',
                                 'txtrecord=new text'],
                     'all': True,
                     'delattr': [],
                     'setattr': []},
            'item_filter': None,
            'method': 'dnsrecord_add',
            'name': ['example.com', {'__dns_name__': 'host1'}]},
        # Idempotency changes
        'idempotent_obj_updates' : idempotent_obj_updates,
    }

    disabled_new_data = 'N/A (en/disable unsupported)'

    exact_existing_data = {
        # Object already exists
        'found_obj' : found_obj,
        # Request object state exactly as specified in module params
        'module_params_updates' : {'state' : 'exact'},
        # Verify dnsrecord_mod API params
        'aom_params' : {
            'item': {'addattr': ['arecord=192.168.42.38',
                                 'txtrecord=new text'],
                     'all': True,
                     'delattr': ['arecord=192.168.42.37',
                                 'mxrecord=10 mx.example.com',
                                 'txtrecord=old text',
                                 'txtrecord=old text 2'],
                     'setattr': []},
            'item_filter': None,
            'method': 'dnsrecord_mod',
            'name': ['example.com', {'__dns_name__': 'host1'}]},
        # Idempotency
        'idempotent_obj' : {
            'arecord': [ "192.168.42.38", "192.168.43.38" ],
            'dn': 'idnsname=host1,idnsname=example.com.,cn=dns,dc=example,dc=com',
            'idnsname': ['host1'],
            'objectClass': ['top', 'idnsrecord'],
            'txtrecord' : ['new text']},
    }

    rem_params = {
        'item': {},
        'item_filter': None,
        'method': 'dnsrecord_del',
        'name': ['example.com', {'__dns_name__': 'host1'}]}
