# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import call, create_autospec, patch
from . import t_st_ipa_abstract

from ansible.modules.identity.ipa.ipa_dnsrecord import DNSRecordIPAClient

class TestDNSRecordIPAClient(t_st_ipa_abstract.AbstractTestClass):

    test_class = DNSRecordIPAClient
    ipa_module = 'ipa_dnsrecord'

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

    find_result = dict(
        dn = "idnsname=host1,idnsname=example.com.,cn=dns,dc=example,dc=com",
        idnsname = [ "host1" ],
        arecord = [ "192.168.42.37", "192.168.43.38" ],
        mxrecord = [ "10 mx.example.com" ],
        txtrecord = [ "old text", "old text 2" ],
        objectClass = [ "top", "idnsrecord" ],
    )

    curr_cleaned = dict(
        arecord = ['192.168.42.37'],
        mxrecord = ['10 mx.example.com'],
        txtrecord = ['old text', 'old text 2'],
    )

    change_cleaned = dict(
        arecord = ['192.168.42.38', '192.168.43.38'],
        txtrecord = ['new text'],
        )

    compute_changes_results = {
        'addattr': {'arecord': ['192.168.42.38'],
                    'txtrecord': ['new text']},
        'delattr': {}}

    find_params = dict(
        method='dnsrecord_find',
        name=['example.com'],
        item=dict(all = True,
                  idnsname = {'__dns_name__':'host1'} ),
        item_filter=None,
    )

    present_existing_params = {
        'item': {'addattr': ['arecord=192.168.42.38',
                             'txtrecord=new text'],
                 'all': True,
                 'delattr': []},
        'item_filter': None,
        'method': 'dnsrecord_mod',
        'name': ['example.com', {'__dns_name__': 'host1'}]}

    present_new_params = {
        'item': {'addattr': ['arecord=192.168.42.38',
                             'arecord=192.168.43.38',
                             'txtrecord=new text'],
                 'all': True,
                 'delattr': []},
        'item_filter': None,
        'method': 'dnsrecord_add',
        'name': ['example.com', {'__dns_name__': 'host1'}]}

    exact_existing_params = {
        'item': {'addattr': ['arecord=192.168.42.38',
                             'txtrecord=new text'],
                 'all': True,
                 'delattr': ['arecord=192.168.42.37',
                             'mxrecord=10 mx.example.com',
                             'txtrecord=old text',
                             'txtrecord=old text 2']},
        'item_filter': None,
        'method': 'dnsrecord_mod',
        'name': ['example.com', {'__dns_name__': 'host1'}]}

    rem_params = {
        'item': {},
        'item_filter': None,
        'method': 'dnsrecord_del',
        'name': ['example.com', {'__dns_name__': 'host1'}]}
