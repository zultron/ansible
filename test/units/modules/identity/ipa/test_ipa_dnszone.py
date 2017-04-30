# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import call, create_autospec, patch
from . import t_st_ipa_abstract

from ansible.modules.identity.ipa.ipa_dnszone import DNSZoneIPAClient

class TestDNSZoneIPAClient(t_st_ipa_abstract.AbstractTestClass):

    test_class = DNSZoneIPAClient

    module_params = dict(
        idnsname = "test.example.com",
        idnsallowdynupdate = True,
        idnsallowtransfer = "none;",
        nsrecord = "host2.example.com.",
        state = "enabled",
        ipa_host = "host1.example.com",
        ipa_user = "admin",
        ipa_pass = "secretpass",
    )

    found_obj = {
        'dn': 'idnsname=test.example.com.,cn=dns,dc=example,dc=com',
        'idnsallowdynupdate': ['FALSE'],
        'idnsallowquery': ['any;'],
        'idnsallowtransfer': ['none;'],
        'idnsname': ['test.example.com.'],
        'idnssoaexpire': ['1209600'],
        'idnssoaminimum': ['3600'],
        'idnssoamname': ['host1.example.com.'],
        'idnssoarefresh': ['3600'],
        'idnssoaretry': ['900'],
        'idnssoarname': ['hostmaster'],
        'idnssoaserial': ['1493244462'],
        'idnsupdatepolicy': ['grant EXAMPLE.COM krb5-self * A;'
                             ' grant EXAMPLE.COM krb5-self * AAAA;'
                             ' grant EXAMPLE.COM krb5-self * SSHFP;'],
        'idnszoneactive': ['TRUE'],
        'nsrecord': ['host1.example.com.'],
        'objectclass': ['idnszone', 'top', 'idnsrecord']}

    find_params = dict(
        method='dnszone_find',
        name=[None],
        item=dict(all = True,
                  idnsname = 'test.example.com' ),
        item_filter=None,
    )

    # These changes make most operations idempotent
    idempotent_obj_updates = {
        'idnsallowdynupdate' : ['TRUE'],
        'idnszoneactive': ['TRUE'],
        'nsrecord' : ['host2.example.com.']}

    present_existing_data = {
        # Object already exists
        'found_obj' : found_obj,
        # Verify dnszone_mod API params
        'aom_params' : {
            'item' : {'delattr': [],
                      'all': True,
                      'setattr': ['idnsallowdynupdate=True',
                                  'nsrecord=host2.example.com.'],
                      'addattr': []},
            'item_filter': None,
            'method' : 'dnszone_mod',
            'name' : ['test.example.com']},
        # Idempotency changes
        'idempotent_obj_updates' : {
            'arecord': ['192.168.42.37', '192.168.43.38'],
            'idnsallowdynupdate': ['TRUE'],
            'nsrecord': ['host2.example.com.'],
        },
    }

    enabled_existing_data = {
        # Object already exists, but disabled
        'found_obj' : found_obj,
        'found_obj_updates' : { 'idnszoneactive': ['FALSE'] },
        # Request object be enabled
        'module_params_updates' : {'state' : 'enabled'},
        # Verify dnszone_mod API params
        'aom_params' : {
            'item' : {'delattr': [],
                      'all': True,
                      'setattr': ['idnsallowdynupdate=True',
                                  'nsrecord=host2.example.com.'],
                      'addattr': []},
            'item_filter': None,
            'method' : 'dnszone_mod',
            'name' : ['test.example.com']},
        # Verify dnszone_enable API params
        'eod_params' : {
            'item' : {},
            'item_filter': None,
            'method' : 'dnszone_enable',
            'name' : ['test.example.com']},
        # Idempotency changes
        'idempotent_obj_updates' : idempotent_obj_updates,
    }

    present_new_data = {
        # Object doesn't yet exist
        'found_obj' : {},
        # Verify dnszone_add API params
        'aom_params' : {
            'item' : {'delattr': [],
                      'all': True,
                      'setattr': ['idnsallowdynupdate=True',
                                  'idnsallowtransfer=none;',
                                  'nsrecord=host2.example.com.'],
                      'addattr': []},
            'item_filter': None,
            'method' : 'dnszone_add',
            'name' : ['test.example.com']},
        # Idempotency
        'idempotent_obj' : found_obj,
        'idempotent_obj_updates' : idempotent_obj_updates,
    }

    disabled_new_data = {
        # Object doesn't yet exist
        'found_obj' : {},
        # Request object be added but disabled
        'module_params_updates' : {'state' : 'disabled'},
        # Verify dnszone_add API params
        'aom_params' : {
            'item' : {'delattr': [],
                      'all': True,
                      'setattr': ['idnsallowdynupdate=True',
                                  'idnsallowtransfer=none;',
                                  'nsrecord=host2.example.com.'],
                      'addattr': []},
            'item_filter': None,
            'method' : 'dnszone_add',
            'name' : ['test.example.com']},
        # Pretend add_or_modify() created found_obj even though this
        # doesn't follow the module params, but for the
        # enable_or_disable() test, it's only important that
        # `idnszoneactive == 'TRUE'`
        'updated_obj' : found_obj,
        # Verify dnszone_disable API params
        'eod_params' : {
            'item' : {},
            'item_filter': None,
            'method' : 'dnszone_disable',
            'name' : ['test.example.com']},
        # Idempotency
        'idempotent_obj' : found_obj,
        'idempotent_obj_updates' : {
            'idnsallowdynupdate' : ['TRUE'],
            'idnszoneactive': ['FALSE'],
            'nsrecord' : ['host2.example.com.']},
    }

    exact_existing_data = {
        # Object already exists
        'found_obj' : found_obj,
        # Request object state exactly as specified in module params
        'module_params_updates' : {'state' : 'exact'},
        # Verify dnszone_mod API params
        'aom_params' : {
            'item' : {'delattr': ['idnsallowquery=any;',
                                  'idnssoaexpire=1209600',
                                  'idnssoaminimum=3600',
                                  'idnssoamname=host1.example.com.',
                                  'idnssoarefresh=3600',
                                  'idnssoaretry=900',
                                  'idnssoarname=hostmaster',
                                  'idnssoaserial=1493244462',
                                  ('idnsupdatepolicy=grant EXAMPLE.COM krb5-self * A;'
                                   ' grant EXAMPLE.COM krb5-self * AAAA;'
                                   ' grant EXAMPLE.COM krb5-self * SSHFP;')],
                      'all': True,
                      'setattr': ['idnsallowdynupdate=True',
                                  'nsrecord=host2.example.com.'],
                      'addattr': []},
            'item_filter': None,
            'method' : 'dnszone_mod',
            'name' : ['test.example.com']},
        # Idempotency
        'idempotent_obj' : {
            'idnsallowdynupdate' : ['TRUE'],
            'idnsallowtransfer' : ['none;'],
            'nsrecord' : ['host2.example.com.']},
    }

    rem_params = {
        'item' : {},
        'method' : 'dnszone_del',
        'name' : ['test.example.com'],
        'item_filter' : None}
