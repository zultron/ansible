# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import call, create_autospec, patch
from . import t_st_ipa_abstract

from ansible.modules.identity.ipa.ipa_dnszone import DNSZoneIPAClient

class TestDNSZoneIPAClient(t_st_ipa_abstract.AbstractTestClass):

    test_class = DNSZoneIPAClient
    ipa_module = 'ipa_dnszone'

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

    find_result = dict(
        dn = "idnsname=test.example.com.,cn=dns,dc=example,dc=com",
        idnsallowdynupdate = [ "FALSE" ],
        idnsallowquery = [ "any;" ],
        idnsallowtransfer = [ "none;" ],
        idnsname = [ "test.example.com." ],
        idnssoaexpire = [ "1209600" ],
        idnssoaminimum = [ "3600" ],
        idnssoamname = [ "host1.example.com." ],
        idnssoarefresh = [ "3600" ],
        idnssoaretry = [ "900" ],
        idnssoarname = [ "hostmaster" ],
        idnssoaserial = [ "1493244462" ],
        idnsupdatepolicy = [ "grant EXAMPLE.COM krb5-self * A;"
                             " grant EXAMPLE.COM krb5-self * AAAA;"
                             " grant EXAMPLE.COM krb5-self * SSHFP;" ],
        idnszoneactive = [ "TRUE" ],
        objectclass = [ "idnszone",
                        "top",
                        "idnsrecord" ],
        nsrecord = [ "host1.example.com." ],
    )

    curr_cleaned = dict(
        idnsallowdynupdate = 'FALSE',
        idnsallowquery = 'any;',
        idnsallowtransfer = 'none;',
        idnssoaexpire = '1209600',
        idnssoaminimum = '3600',
        idnssoamname = 'host1.example.com.',
        idnssoarefresh = '3600',
        idnssoaretry = '900',
        idnssoarname = 'hostmaster',
        idnssoaserial = '1493244462',
        idnsupdatepolicy = ('grant EXAMPLE.COM krb5-self * A; '
                            'grant EXAMPLE.COM krb5-self * AAAA; '
                            'grant EXAMPLE.COM krb5-self * SSHFP;'),
        idnszoneactive = 'TRUE',
        nsrecord = 'host1.example.com.',
    )

    change_cleaned = dict(
        idnsallowdynupdate = True,
        idnsallowtransfer = "none;",
        nsrecord = "host2.example.com.",
        )

    compute_changes_results = {
        'setattr': {'idnsallowdynupdate': [True],
                     'nsrecord': ['host2.example.com.']},
        'delattr': {},
        'addattr': {}}

    find_params = dict(
        method='dnszone_find',
        name=[None],
        item=dict(all = True,
                  idnsname = 'test.example.com' ),
        item_filter=None,
    )

    enabled_existing_params = {
        'item' : {'delattr': [],
                  'all': True,
                  'setattr': ['idnsallowdynupdate=True',
                              'nsrecord=host2.example.com.'],
                  'addattr': []},
        'item_filter': None,
        'method' : 'dnszone_mod',
        'name' : ['test.example.com']}

    disabled_new_params = {
        'item' : {'delattr': [],
                  'all': True,
                  'setattr': ['idnsallowdynupdate=True',
                              'idnsallowtransfer=none;',
                              'idnszoneactive=FALSE',
                              'nsrecord=host2.example.com.'],
                  'addattr': []},
        'item_filter': None,
        'method' : 'dnszone_add',
        'name' : ['test.example.com']}

    exact_existing_params = {
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
        'name' : ['test.example.com']}

    rem_params = {
        'item' : {},
        'method' : 'dnszone_del',
        'name' : ['test.example.com'],
        'item_filter' : None}
