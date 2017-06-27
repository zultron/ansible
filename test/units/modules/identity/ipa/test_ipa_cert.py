# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from . import AbstractTestClass, IPATestError

from ansible.modules.identity.ipa.ipa_cert import CertIPAClient

class TestCertIPAClient(unittest.TestCase, AbstractTestClass):

    test_class = CertIPAClient

    # Track state from test to test
    current_state = {}

    # cert:  completely bogus; not used in live IPA test
    cert = 'LS0tLUZBS0UgQ0VSVCBEQVRBLS0tLQo='
    # req:  must be legit (enough)
    # - generate:
    # echo -ne "\n\n\n\n\ntest_cert_user\ntest_cert_user@example.com\n\n\n" | \
    #     openssl req -nodes -newkey rsa:1024 -rand /dev/urandom \
    #         -keyout /dev/null -out req.pem -days 3650 >/dev/null
    # - check:
    # openssl req -in req.pem -noout -text
    req = '''
        -----BEGIN CERTIFICATE REQUEST-----
        MIIByjCCATMCAQAwgYkxCzAJBgNVBAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRl
        MSEwHwYDVQQKDBhJbnRlcm5ldCBXaWRnaXRzIFB0eSBMdGQxFzAVBgNVBAMMDnRl
        c3RfY2VydF91c2VyMSkwJwYJKoZIhvcNAQkBFhp0ZXN0X2NlcnRfdXNlckBleGFt
        cGxlLmNvbTCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkCgYEA1aYto6IRPAnRGqfG
        neJ4EcMS4vdmDBxCvm/V1eu6TDem54ozK01EvpKbmK6YpsXeIdAYA3lQT2HQKhFG
        f1ZoWdI0Pb/2KjONQEimid5WRrWXz91KTAwNiXAAp/ukmMCy+iKRvWwKB5uBDVFz
        o8GB6BXn1J9qebEXhWUvfSi+uVkCAwEAAaAAMA0GCSqGSIb3DQEBCwUAA4GBAFIa
        t60hMLIKXwP/UtYJz00C/KO6scXutc8Uusly2vf9F/Rj6V7D3+HDMWXwjE4Brm/2
        hai19ENC9F3hKCf6azA/8DC+EqaPxl934sGN94LCLwjb8RsD9LnC8WXWfcFsux4a
        8rGirj2cun92hSYbDUt9iG74SpzKgdK3q7nBTVsC
        -----END CERTIFICATE REQUEST-----
    '''

    # Test CA name
    ca_name = 'test_cert_ca'
    # Test user name
    user_name = 'test_cert_user'

    find_request = dict(
        method='cert_find',
        name=[],
        item=dict(all = True,
                  subject = user_name,
                  exactly = True,
                  cacn = ca_name),
    )

    @classmethod
    def setup_class(cls):
        # Set up CA, user

        # Only need to set up if using a real live host
        if not cls.live_host: return

        # Get test class instance
        client = cls.get_tst_class()
        # Log in
        client.login()
        # Create CA object
        try:
            client._post_json(
                name = [cls.ca_name],
                item = {'description': 'For testing cert objects',
                        'ipacasubjectdn': 'CN=Test Cert CA,O=%s' % (
                            cls.ipa_domain.upper()),
                        'all': True},
                method = 'ca_add',
                )
        except IPATestError:
            pass
        # Create user object
        try:
            client._post_json(
                name = [cls.user_name],
                item = {'cn': 'test cert user',
                        'givenname': 'Test',
                        'sn': 'User',
                        'mail': [ '%s@example.com' % cls.user_name ],
                        'all': True},
                method = 'user_add',
                )
        except IPATestError:
            pass

    def test_10_cert_present_new(self):
        client = self.runner(
            test_key = 10,
            module_params = dict(
                principal = self.user_name,
                cacn = self.ca_name,
                req = self.req,
                state = "present",
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
                        'item': {
                            'cacn': self.ca_name,
                            'principal': self.user_name,
                            'all': True},
                        'method': 'cert_request',
                        'name': [ self.req ] },
                    reply = {
                        "cacn": self.ca_name,
                        'certificate' : self.cert,
                        "serial_number": 42,
                        'subject': 'CN=%s,O=%s' % (
                            self.user_name, self.ipa_domain.upper()),
                        'status': 'VALID',
                    },
                ),
                # No enable/disable operation
            ],
        )
        self.current_state['cert_sn'] = client.requests[-1]['response'].get(
            'serial_number',None)

    def test_11_cert_absent_revoke(self):
        sn = self.current_state.get('cert_sn', None)
        if sn is None:
            raise unittest.SkipTest(
                "Certificate serial number not available")
        self.runner(
            test_key = 11,
            module_params = dict(
                principal = self.user_name,
                cacn = self.ca_name,
                state = "absent",  # Revoke
                serial_number = sn,
                revocation_reason = 4, # (superceded)
            ),
            post_json_calls = [
                dict(
                    name = 'find existing cert',
                    request = dict(
                        method='cert_find',
                        name=[],
                        item=dict(all = True,
                                  subject = self.user_name,
                                  cacn = self.ca_name,
                                  max_serial_number = sn,
                                  min_serial_number = sn,
                                  exactly = True,
                              ),
                    ),
                ),
                dict(
                    name = 'revoke existing cert',
                    request = {
                        'name': [ sn ],
                        'item': {
                            'cacn': self.ca_name,
                            'revocation_reason': 4},
                        'method': 'cert_revoke' },
                    reply = {},
                ),
                # No enable/disable operation
            ],
        )

    def test_12_cert_cacert(self):
        self.test_changed = False
        self.runner(
            test_key = 12,
            module_params = dict(
                principal = "CN=Certificate Authority,O=%s" % (
                    self.ipa_domain.upper()),
                cacn = "ipa",
                state = "present",
            ),
            post_json_calls = [
                dict(
                    name = 'find CA cert',
                    request = dict(
                        method='cert_find',
                        name=[],
                        item=dict(all = True,
                                  subject = "Certificate Authority",
                                  cacn = "ipa",
                                  exactly = True,
                              ),
                    ),
                ),
            ],
        )
