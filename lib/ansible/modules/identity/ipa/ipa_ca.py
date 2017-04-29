ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ipa_ca
author: John Morris (@zultron)
short_description: Manage FreeIPA CAs
description:
- Add, delete and modify CAs within IPA server
options:
  cn:
    description: CA name
    required: true
    aliases: ['name']
  ipacasubjectdn:
    description: Subject Distinguished Name
    required: false
  description:
    description: Description of the purpose of the CA
    required: false
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
ca:
  description: ca as returned by IPA API
  returned: always
  type: dict
'''

from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.ipa import IPAClient

class CAIPAClient(IPAClient):
    name = 'ca'

    methods = dict(
        add = '%s_add',
        rem = '%s_del',
        mod = '%s_mod',
        find = '%s_find',
        show = '%s_show',
        )

    kw_args = dict(
        cn = dict(type='str', required=True, aliases=['name'],
                  when_name=['add','mod','rem'], when=['find']),
        ipacasubjectdn = dict(
            type='str', required=False, when=['add']),
        description = dict(
            type='str', required=False),
    )

def main():
    CAIPAClient().main()

if __name__ == '__main__':
    main()
