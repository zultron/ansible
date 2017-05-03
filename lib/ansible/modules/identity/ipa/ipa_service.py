ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ipa_service
author: John Morris (@zultron)
short_description: Manage FreeIPA services
description:
- Add, delete and modify services within IPA server
options:
  krbprincipalname:
    description: Kerberos principal name
    required: true
    aliases: ['name']
  managed_by:
    description:
      - List of hosts that can manage this service
      - When this option is given, the C(state) option applies to this
        list of hosts.
    required: false
  state:
    description:
      - State to ensure
      - If the C(managed_by) option is not supplied, C(state=absent) ensures
        the service itself is absent, and otherwise it ensures the listed
        hosts are absent from C(managed_by).
      - C(state=present) applies to both the service itself and C(managed_by)
        hosts.
    required: false
    default: present
    choices: ["present", "absent"]
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
# Create LDAP service
- ipa_service:
    krbprincipalname: ldap/host1.example.com@EXAMPLE.COM
    state: present
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Remove LDAP service
- ipa_service:
    krbprincipalname: ldap/host1.example.com@EXAMPLE.COM
    state: absent
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret

# Allow host2 to manage host1 LDAP service
- ipa_service:
    krbprincipalname: ldap/host1.example.com@EXAMPLE.COM
    state: present
    managed_by: [ host2.example.com ]
    ipa_host: ipa.example.com
    ipa_user: admin
    ipa_pass: topsecret
'''

RETURN = '''
service:
  description: service as returned by IPA API
  returned: always
  type: dict
'''

from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.ipa import IPAClient
import re


class ServiceIPAClient(IPAClient):
    name = 'service'

    methods = dict(
        add = '%s_add',
        rem = '%s_del',
        mod = '%s_mod',
        find = '%s_find',
        show = '%s_show',
        )

    kw_args = dict(
        krbcanonicalname = dict(
            type='str', required=True, aliases=['name'],
            when=['find'], when_name=['add', 'mod', 'rem']),
        certificate = dict(
            type='str', required=False, from_result_attr='usercertificate'),
        krbprincipalauthind = dict(
            type='str', required=False),

        # The next three booleans are bits broken out of the
        # krbticketflags param; see filter_value() and request_cleanup()
        ipakrbrequirespreauth = dict(
            type='bool', required=False),
        ipakrbokasdelegate = dict(
            type='bool', required=False),
        ipakrboktoauthasdelegate = dict(
            type='bool', required=False),

        # service-add-principal CANONICAL-PRINCIPAL PRINCIPAL...
        krbprincipalname = dict(
            type='list', required=False),

        # The host and create/retrieve_keytab_* params require the DIT
        # base DN (e.g. 'dc=example,dc=com') to reconstruct
        # user/group/host/hostgroup DNs from uid/cn/fqdn/cn ; see
        # filter_value() and request_cleanup(); e.g.:
        #
        # write_keytab_users: admin ->
        # ipaAllowedToPerform;write_keys:
        #     uid=admin,cn=users,cn=accounts,dc=example,dc=com
        #
        # read_keytab_hosts: host1.example.com ->
        # ipaAllowedToPerform;read_keys:
        #     fqdn=host1.example.com,cn=computers,cn=accounts,dc=example,dc=com
        directory_base_dn = dict(
            type='str', required=False, when=[]),

        # managedby attribute value
        host = dict(type='list', required=False),

        # service-allow-create-keytab users/groups/hosts/hostgroups
        # ipaAllowedToPerform;write_keys:
        write_keytab_users = dict(
            type='list', required=False),
        write_keytab_groups = dict(
            type='list', required=False),
        write_keytab_hosts = dict(
            type='list', required=False),
        write_keytab_hostgroups = dict(
            type='list', required=False),

        # service-allow-read-keytab  users/groups/hosts/hostgroups
        # ipaAllowedToPerform;read_keys:  as above
        read_keytab_users = dict(
            type='list', required=False),
        read_keytab_groups = dict(
            type='list', required=False),
        read_keytab_hosts = dict(
            type='list', required=False),
        read_keytab_hostgroups = dict(
            type='list', required=False),
    )

    def filter_value(self, key, val, dirty, item):
        if key == 'krbprincipalname':
            # krbprincipalname list:  This list of principal aliases
            # always includes the principal canonical name.  Aliases
            # specified in this list should avoid touching that value.
            item[key] = list(val)
            item[key].remove(self.module.params.get('krbcanonicalname'))
            return True

        if key.startswith('write_keytab') or key.startswith('read_keytab'):
            # Filter account DNs of the right type and return the uid/cn/fqdn
            #
            # uid=admin,cn=users,cn=accounts,dc=example,dc=com
            # cn=editors,cn=groups,cn=accounts,dc=example,dc=com
            # fqdn=host1.example.com,cn=computers,cn=accounts,dc=example,dc=com
            # cn=ipaservers,cn=hostgroups,cn=accounts,dc=example,dc=com

            # Account type:  2nd element of DN
            acct_type = key.split('_')[2]
            if acct_type == 'hosts':  acct_type = 'computers'
            # For DNs matching the account type, extract the 1st element
            item[key] = []
            for v in val:
                m = re.match(
                    r'^(?:fqdn|cn|uid)=([^,]*),cn=%s,cn=accounts,' % acct_type,
                    v)
                if m is not None:
                    item[key].append(m.group(1))
            return True

        if key == 'managedby':
            # managedby attribute value:
            # fqdn=host1.example.com,cn=computers,cn=accounts,dc=example,dc=com
            for v in val:
                m = re.match( r'fqdn=([^,]*),cn=computers,cn=accounts', v)
                if m is not None:
                    item.setdefault('host',[]).append(m.group(1))
            return True

        # These are broken out of the krbticketflags param of the reply
        if key == 'krbticketflags':
            item['ipakrbrequirespreauth']    = ( [bool( val[0] & 128     )] )
            item['ipakrbokasdelegate']       = ( [bool( val[0] & 1048576 )] )
            item['ipakrboktoauthasdelegate'] = ( [bool( val[0] & 2097152 )] )
            return True


    def request_cleanup(self, request):
        # Allow krbticketflags and ipaAllowedToPerform;read/write_keys
        # request parameters to be composed from multiple other params
        # that are simpler to deal with in a task spec

        # krbticketflags:
        # Don't add this to the request unless there was a change
        have_krbticketflags = False
        ktf_old = krbticketflags = self.found_obj.get('krbticketflags',[0])[0]
        for req_op, is_del in ((request['item']['setattr'], False),
                               (request['item']['delattr'], True)):
            for key, mult in (('ipakrbrequirespreauth', 128),
                              ('ipakrbokasdelegate', 1048576),
                              ('ipakrboktoauthasdelegate', 2097152)):
                if key in req_op:
                    val = req_op.pop(key)[0]
                    if not val: complement = not is_del
                    else: complement = is_del
                    if is_del and not val:
                        # Absent 'ipakrb*: False' doesn't make sense,
                        # since the bit is still there; call this an
                        # error
                        self._fail(key, 'Unable to make False value absent')
                    elif complement:
                        krbticketflags &= ~(mult)
                    else:
                        krbticketflags |= (mult)
                    have_krbticketflags = True
        if have_krbticketflags:
            request['item']['setattr']['krbticketflags'] = [krbticketflags]
            request['item']['delattr'].pop('krbticketflags',None)

        # ipaAllowedToPerform;write_keys:
        directory_base_dn = self.module.params.get('directory_base_dn',None)
        dn_pat = 'uid=%s,cn=%s,cn=accounts,%s'
        for thing in ('users', 'groups', 'hosts', 'hostgroups'):
            for perm in ('read', 'write'):
                key = '%s_keytab_%s' % (perm, thing)
                for req_op in (request['item']['addattr'],
                               request['item']['delattr']):
                    if key not in req_op: continue
                    # directory_base_dn must be defined
                    if directory_base_dn is None:
                        self._fail(key, 'directory_base_dn param undefined')
                    # Patch values into ipaallowedtoperform;read/write_keys
                    dest_key = 'ipaallowedtoperform;%s_keys'%perm
                    for val in req_op.pop(key):
                        req_op.setdefault(dest_key,[]).append(
                            dn_pat % (val, thing, directory_base_dn))

        # host -> managedby:
        for act_key, acts in request['item'].items():
            for host in acts.pop('host',[]):
                if 'directory_base_dn' not in self.module.params:
                    self._fail('host', 'Must specify directory_base_dn with host')
                    break
                acts.setdefault('managedby',[]).append(
                    'fqdn=%s,cn=computers,cn=accounts,%s' %
                    (host, self.module.params['directory_base_dn']))

def main():
    client = ServiceIPAClient().main()


if __name__ == '__main__':
    main()
