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

    # Fake cert and req data
    cert = 'LS0tLUZBS0UgQ0VSVCBEQVRBLS0tLQo='
    # echo -ne "\n\n\n\n\ntest_user\ntest_user@example.com\n\n\n" | \
    #     openssl req -nodes -newkey rsa:2048 -rand /dev/urandom \
    #         -keyout key.pem -out req.pem -days 365
    # openssl req -in req.pem -noout -text
    req = '''
        -----BEGIN CERTIFICATE REQUEST-----
        MIICxDCCAawCAQAwfzELMAkGA1UEBhMCQVUxEzARBgNVBAgMClNvbWUtU3RhdGUx
        ITAfBgNVBAoMGEludGVybmV0IFdpZGdpdHMgUHR5IEx0ZDESMBAGA1UEAwwJdGVz
        dF91c2VyMSQwIgYJKoZIhvcNAQkBFhV0ZXN0X3VzZXJAZXhhbXBsZS5jb20wggEi
        MA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDXNHC+SvXPCeLtVmNPCrTcPlDm
        S+RHVewpjAZygagfx8Nt7dthmVDyJ6XVD6dzi2lQ7RQ4lN0BGzDqH60YIT59cyKg
        5tKMNyrWd3xonKdL4cKvtY6GmEAfJiundx7iWJCz1P1JIOSam2Hr2TnVd3UKvvWu
        /oYKDLeDvk+jUFbAHBc02x5hDFV0iByxHWl1pn4B7F4epesfIXYMW+u5AU3AxsZo
        knLD3Fvbp0HO4LbsugKrNcScI7Yn5Ft+YhLYw+jH20HKif/hYjkLmrDz4x1Y8oDv
        51Yj/ZxsmeKZ4vEHvyYqRhWux1gjWHZcC6QvZp8xrkZnNmJq1paigT2BzKtLAgMB
        AAGgADANBgkqhkiG9w0BAQsFAAOCAQEACF4cLIqvJJUkIeFvKaSCyZ7VnPcEZwKs
        LKuoaBn/3+WPdK3t7hlV24R7hMJzlDM/dHeVYbOc1/QPeytt00/Gxxc4RcsI1dUz
        gbgqGfHCTQctbdqCGaC3vdvlhBuFjF5bxhaHCATD/sw1GJATJnvYDoblS6mY756V
        vlbu6My787BQJg/95VKJKeyV8y2kMdQEPDg/uA2ECCM0JIZQW0ZkXnwopg1/DQha
        wIlGGm+5AQwGLUGz1Edy55XlgXa9apOIpgE26SQ07mXAx5EtzQcIizH5aP7vWXS2
        vQwO7s5kOWs1M6kmzhQW0HemGkHQN7GNb7EFsrxCguF4XxBtqnVW3Q==
        -----END CERTIFICATE REQUEST-----
        '''

    # Test CA name
    ca_name = 'test_cert_ca'
    # Test user name
    user_name = 'test_user'

    find_request = dict(
        method='cert_find',
        name=[],
        item=dict(all = True,
                  subject = user_name,
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
                ipa_host = self.ipa_host,
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
        self.runner(
            test_key = 11,
            module_params = dict(
                principal = self.user_name,
                cacn = self.ca_name,
                state = "absent",  # Revoke
                serial_number = sn,
                revocation_reason = 4, # (superceded)
                ipa_host = self.ipa_host,
                ipa_user = "admin",
                ipa_pass = "secretpass",
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
