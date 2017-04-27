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

    mod_params = dict(
        idnsname = "test.example.com",
        state = "enabled",
        idnsallowtransfer = "none;",
        ipa_host = "host1.example.com",
        ipa_user = "admin",
        ipa_pass = "secretpass",
    )

    find_params = dict(
        method='dnszone_find',
        name=None,
        item=dict(idnsallowtransfer = 'none;', all = True,
                  idnsname = 'test.example.com' ),
        item_filter=None,
    )

    find_result = {
            "dn": "idnsname=test.example.com.,cn=dns,dc=example,dc=com", 
            "idnsallowdynupdate": [
                "FALSE"
            ], 
            "idnsallowquery": [
                "any;"
            ], 
            "idnsallowtransfer": [
                "none;"
            ], 
            "idnsname": [
                "test.example.com."
            ], 
            "idnssoaexpire": [
                "1209600"
            ], 
            "idnssoaminimum": [
                "3600"
            ], 
            "idnssoamname": [
                "host1.example.com."
            ], 
            "idnssoarefresh": [
                "3600"
            ], 
            "idnssoaretry": [
                "900"
            ], 
            "idnssoarname": [
                "hostmaster"
            ], 
            "idnssoaserial": [
                "1493244462"
            ], 
            "idnsupdatepolicy": [
                "grant EXAMPLE.COM krb5-self * A;"
                " grant EXAMPLE.COM krb5-self * AAAA;"
                " grant EXAMPLE.COM krb5-self * SSHFP;"
            ], 
            "idnszoneactive": [
                "TRUE"
            ], 
            "nsrecord": [
                "host1.example.com."
            ], 
            "objectclass": [
                "idnszone", 
                "top", 
                "idnsrecord"
            ]
        }

