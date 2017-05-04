# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from . import AbstractTestClass

from ansible.modules.identity.ipa.ipa_cert import CertIPAClient

class TestCertIPAClient(unittest.TestCase, AbstractTestClass):

    test_class = CertIPAClient

    # Track state from test to test
    current_state = {}

    find_request = dict(
        method='cert_find',
        name=[None],
        item=dict(all = True,
                  subject = 'host1.example.com',
                  cacn = 'test_ca'),
    )

    # Fake cert and req data
    cert = 'LS0tLUZBS0UgQ0VSVCBEQVRBLS0tLQo='
    req = 'LS0tLUZBS0UgQ0VSVCBSRVEgREFUQS0tLS0K'

    def test_10_cert_present_new(self):
        self.runner(
            test_key = 10,
            module_params = dict(
                principal = "host1.example.com",
                cacn = "test_ca",
                req = self.req,
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
                        'item': {'cacn': 'test_ca',
                                 'principal': 'host1.example.com'},
                        'method': 'cert_request',
                        'name': [ self.req ] },
                    reply = {
                        "cacn": "test_ca",
                        'certificate' : self.cert,
                        "serial_number": 42,
                        'subject': 'CN=host1.example.com,O=EXAMPLE.COM',
                        'status': 'VALID',
                    },
                ),
                # No enable/disable operation
            ],
        )


    def test_11_cert_absent_revoke(self):
        self.runner(
            test_key = 11,
            module_params = dict(
                principal = "host1.example.com",
                cacn = "test_ca",
                state = "absent",  # Revoke
                serial_number = 42,
                revocation_reason = 4, # (superceded)
                ipa_host = "host1.example.com",
                ipa_user = "admin",
                ipa_pass = "secretpass",
            ),
            post_json_calls = [
                dict(
                    name = 'find existing cert',
                    request = dict(
                        method='cert_find',
                        name=[None],
                        item=dict(all = True,
                                  subject = 'host1.example.com',
                                  cacn = 'test_ca',
                                  max_serial_number = 42,
                                  min_serial_number = 42,
                              ),
                    ),
                ),
                dict(
                    name = 'revoke existing cert',
                    request = {
                        'name': [ 42 ],
                        'item': {'cacn': 'test_ca',
                                 'revocation_reason': 4},
                        'method': 'cert_revoke' },
                    reply = {},
                ),
                # No enable/disable operation
            ],
        )
