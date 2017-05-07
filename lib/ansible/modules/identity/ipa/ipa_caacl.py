ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ipa_caacl
author: John Morris (@zultron)
short_description: Manage FreeIPA CA ACLs
description:
- Add, delete and modify CA ACLs within IPA server
options:
  cn:
    description: CA ACL name
    required: true
    aliases: ['name']
  description:
    description: Description
    required: false
  user:
    description: List of user members
    required: false
  group:
    description: List of group members
    required: false
  host:
    description: List of target hosts
    required: false
  hostgroup:
    description: List of target hostgroups
    required: false
  service:
    description: List of services
    required: false
  certprofile:
    description: List of certificate profiles
    required: false
  ca:
    description: List of certificate authorities
    required: false
  state:
    description: State to ensure
    required: false
    default: present
    choices: ["present", "absent", "exact", "enabled", "disabled"]
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
# Create LDAP caacl
- ipa_caacl:
    krbprincipalname: ldap/host1.example.com@EXAMPLE.COM
    state: present
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Remove LDAP caacl
- ipa_caacl:
    krbprincipalname: ldap/host1.example.com@EXAMPLE.COM
    state: absent
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Allow host2 to manage host1 LDAP caacl
- ipa_caacl:
    krbprincipalname: ldap/host1.example.com@EXAMPLE.COM
    state: present
    managed_by: [ host2.example.com ]
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
'''

RETURN = '''
caacl:
  description: caacl as returned by IPA API
  returned: always
  type: dict
'''

from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.ipa import IPAClient

class CAACLIPAClient(IPAClient):
    name = 'caacl'

    kw_args = dict(
        # common params
        cn = dict(
            type='str', required=True, aliases=['name'], when=['find'],
            when_name=['add', 'mod', 'rem', 'enabled', 'disabled']),
        # add/mod params
        description = dict(
            type='str', required=False, when=['add', 'mod'],
            ),
        ipaenabledflag = dict(
            type='bool', required=False, enablekey=True),
        # add/rem list params
        user = dict(
            type='list', required=False,
            from_result_attr='memberuser_user'),
        group = dict(
            type='list', required=False,
            from_result_attr='memberuser_group'),
        host = dict(
            type='list', required=False,
            from_result_attr='memberhost_host'),
        hostgroup = dict(
            type='list', required=False,
            from_result_attr='memberhost_hostgroup'),
        service = dict(
            type='list', required=False,
            from_result_attr='memberservice_service'),
        certprofile = dict(
            type='list', required=False,
            from_result_attr='ipamembercertprofile_certprofile'),
        ca = dict(
            type='list', required=False,
            from_result_attr='ipamemberca_ca'),
    )

    def request_cleanup(self, request):
        # caacl user/host/service/etc. list attributes can't be
        # manipulated with addattr/delattr, and need separate requests
        # with separate methods for each

        # Extract and save separate requests for posting later
        self.request_items = {}
        # Values in 'addattr' will go to caacl_add_*, and 'delattr' to
        # caacl_remove_*
        for from_op, to_op in (('addattr','add'),
                               ('delattr','remove')):
            # Methods e.g. caacl_add_host have parameters e.g. user
            # and group
            for attr_cat, attrs in (('user',('user','group')),
                                    ('host',('host','hostgroup')),
                                    ('profile',('certprofile',)),
                                    ('ca',('ca',)),
                                    ('service',('service',))):
                for attr in attrs:
                    method = 'caacl_%s_%s' % (to_op, attr_cat)
                    val = request['item'].get(from_op,{}).pop(attr,[])
                    if val:
                        self.request_items.setdefault(method,{})[attr] = (
                            sorted(val))
                        self.request_items[method]['all'] = True
        # Save request name for easy access
        self.request_name = request['name']
                    
    def other_requests(self):
        # Execute additional requests

        if len(self.request_items.keys()) > 0:
            self.changed = True

        if self.module.check_mode or not self.changed:
            return

        self.other_request_objs = []
        # (Sorted for unit tests)
        for method in sorted(self.request_items.keys()):
            request = dict(
                method = method,
                item = self.request_items[method],
                name = self.request_name,
            )
            self.final_obj = self._post_json(**request)
            self.other_request_objs.append(self.final_obj)

def main():
    CAACLIPAClient().main()

if __name__ == '__main__':
    main()


# ipa: INFO: Request: {
#     "id": 0, 
#     "method": "caacl_remove_user/1", 
#     "params": [
#         [
#             "user_cert_acl"
#         ], 
#         {
#             "all": true, 
#             "group": [
#                 "editors"
#             ], 
#             "version": "2.213"
#         }
#     ]
# }


# ipa: INFO: Request: {
#     "id": 0,
#     "method": "caacl_add_user/1",
#     "params": [
#         [
#             "user_cert_acl"
#         ],  
#         {
#             "all": true,
#             "group": [
#                 "editors"
#             ],  
#             "version": "2.213"
#         }   
#     ]   
# }   

# ipa: INFO: Request: {
#     "id": 0,  
#     "method": "caacl_add_profile/1", 
#     "params": [
#         [
#             "user_cert_acl"
#         ], 
#         {
#             "all": true, 
#             "certprofile": [
#                 "IECUserRoles"
#             ], 
#             "version": "2.213"
#         }
#     ]
# }

