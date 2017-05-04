ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ipa_cert
author: John Morris (@zultron)
short_description: Manage FreeIPA certificates
description:
- Request and revoke certificates within IPA server
options:
  subject:
    description:
      - Subject (CN) of principal DN
      - Used to find cert and in cert requests
    required: true
  req:
    description:
      - Certificate request; used for C(state=present) to request a cert
      - As generated by C(openssl req)
      - Set CN same as C(subject) option
    required: false
  cacn:
    description:  IPA CA or sub-CA name for request or revoke
    required: false
    default: "ipa"
  principal:
    description:  Principal for this certificate (e.g. HTTP/test.example.com);
                  subject option should match CN; used in cert requests
    required: false
  serial_number:
    description: Cert serial number; used for C(state=absent) to revoke a cert
  revocation_reason:
    description: Reason for revoking cert (See legend with C(ipa help cert))
    required: false
    default: 0
    choices: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
  state:
    description: State to ensure
    required: false
    default: present
    choices: ["present", "absent", "exact"]
  ipa_port:
    description: Port of IPA server
    required: false
    default: 443
  ipa_host:
    description: IP or hostname of IPA server
    required: false
    default: "ipa.example.com"
  ipa_user:
    description: Administrative account used on IPA server
    required: false
    default: "admin"
  ipa_pass:
    description: Password of administrative user
    required: true
  ipa_prot:
    description: Protocol used by IPA server
    required: false
    default: "https"
    choices: ["http", "https"]
  validate_certs:
    description:
    - This only applies if C(ipa_prot) is I(https).
    - If set to C(no), the SSL certificates will not be validated.
    - This should only set to C(no) used on personally controlled
      sites using self-signed certificates.
    required: false
    default: true
version_added: "2.3"
'''

EXAMPLES = '''
# Create 'vpn' ca
- ipa_c:
    name: vpn
    subject: CN=VPN Certificate Authority,O=EXAMPLE.COM
    state: present
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Remove 'vpn' ca
- ipa_ca:
    name: vpn
    state: absent
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
'''

RETURN = '''
cert:
  description: cert as returned by IPA API
  returned: always
  type: dict
'''

from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.ipa import IPAClient

import re

class CertIPAClient(IPAClient):

    # Object name
    name = 'cert'

    # No mod, enable, disable
    methods = dict(
        add = '{}_request',
        mod = '{}_request',
        rem = '{}_revoke',
        find = '{}_find',
        show = '{}_show',
    )

    # ipa -vv cert-find --all --min-serial-number=13 --max-serial-number=13 --ca=test_ca
    # ipa -vv cert-request req.pem --ca=test_ca --principal=bootstrap --profile-id=IECUserRoles
    # ipa -vv cert-revoke 12 --ca=test_ca --revocation-reason=0

    # Filter out expired or revoked certs
    def find_filter(self, i):
        return i['status'] == 'VALID'

    kw_args = dict(
        # common params
        principal = dict(
            type='str', required=True, when=['add', 'find'], ),
        cacn = dict(
            type='str', default='ipa', when=['add','rem','find']),
        # "request" params
        req = dict(
            type='str', required=False, when_name=['add'], when=[]),
        # "revoke" params
        serial_number = dict(
            type='str', required=False, when_name=['rem'], when=[]),
        revocation_reason = dict(
            type='int', required=False, when=['rem'], choices=range(11)),
    )

    def filter_value(self, key, val, dirty, item, action):
        if action == 'find' and key == 'principal':
            # find() uses 'subject' as key, not 'principal', unlike
            # request()
            item['subject'] = val
            return True

        if key == 'subject':
            print "subject = %s" % val
            # Extract principal param from subject
            m = re.match(r'CN=([^,]*),O=', val[0])
            item['principal'] = val if m is None else m.group(1)
            return True

    def expand_changes(self, request):
        # Override base class method
        pass

    def request_cleanup(self, request):
        # Major munge, since the cert object doesn't follow the
        # typical IPA object pattern at all

        # Replace the 'item' part of the request with {key:val,...}
        # pairs normally in the 'setattr' dict...
        item = request['item'] = request['item']['setattr']
        # ...and take values out of list format
        print "item:  %s" % item
        for key in item:
            item[key] = item[key][0]

    def rem_request_cleanup(self, request):
        item = request['item']
        # Take values out of list format
        print "item:  %s" % item
        for key in item:
            item[key] = item[key][0]

    def find_request_cleanup(self, request):
        # In a find() request for state 'absent', add
        # min/max-serial-number
        item = request['item']
        if self.state == 'absent' \
           and 'serial_number' in self.module.params:
            sn = self.module.params['serial_number']
            item['min_serial_number'] = item['max_serial_number'] = sn

def main():
    client = CertIPAClient().main()


if __name__ == '__main__':
    main()
