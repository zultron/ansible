# -*- coding: utf-8 -*-
# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c) 2016 Thomas Krahn (@Nosmoht)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

try:
    import json
except ImportError:
    import simplejson as json

import re

from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.six import PY3
from ansible.module_utils.six.moves.urllib.parse import quote
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.basic import AnsibleModule


class IPAClient(object):

    # Object name: must be overridden
    name = 'unnamed'

    # Parameters for finding existing objects:  must be overridden
    #
    # - additional args to add to search
    # extra_find_args = dict(exactly=True)
    extra_find_args = dict()
    # - for list results, a function to select relevant results
    # find_filter = lambda x: [...]
    find_filter = None

    # Map method names in base object:  may be overridden
    # - Pattern will be filled with class `name` attribute
    methods = dict(
        add = '{}_add',
        rem = '{}_del',
        mod = '{}_mod',
        find = '{}_find',
        show = '{}_show',
        enabled = '{}_enable',
        disabled = '{}_disable',
        )

    # Keyword args:  must be overridden
    # kw_args = dict(
    #     description = dict(
    #         type='str', required=False),
    # )
    kw_args = dict()


    def __init__(self):
        # Process module parameters
        self.init_methods()
        self.init_standard_params()
        self.init_kw_args()

        # Init module object
        self.init_module()

    def init_methods(self):
        self._methods = dict(map(
            lambda x: (x[0],x[1].format(self.name)),
            self.__class__.methods.items()))

    def init_standard_params(self):
        self.argument_spec = dict(
            state=dict(
                type='str', required=False, default='present',
                choices=(['present', 'absent']
                         + (['exact'] if 'mod' in self._methods else [])
                         + (['enabled', 'disabled'] if 'enable' in self._methods
                            else []))),
            ipa_prot=dict(
                type='str', required=False, default='https',
                choices=['http', 'https']),
            ipa_host=dict(
                type='str', required=False,
                default='ipa.example.com'),
            ipa_port=dict(
                type='int', required=False, default=443),
            ipa_user=dict(
                type='str', required=False, default='admin'),
            ipa_pass=dict(
                type='str', required=True, no_log=True),
            validate_certs=dict(
                type='bool', required=False, default=True),
        )

    def init_kw_args(self):
        self.param_data = {}
        self.param_key_map = {}
        self._name_map = {}
        self.enablekey = None
        for name, spec_orig in self.kw_args.items():
            spec = spec_orig.copy()
            self.param_data[name] = dict(
                type = spec['type'],
                when = spec.pop('when', ['add','mod']),
                when_name = spec.pop('when_name', []),
                req_key = spec.pop('req_key', None),
                value_filter_func = spec.pop('value_filter_func', None),
                value_filter_re = (re.compile(spec.pop('value_filter_re')) \
                                   if 'value_filter_re' in spec else None),
            )
            for k in spec_orig.get('when_name',[]):
                name_map = self._name_map.setdefault(k,[None,{}])
                if 'req_key' in spec_orig:
                    name_map[1][name] = spec_orig['req_key']
                else:
                    name_map[0] = name
            if spec.pop('enablekey',False):
                self.enablekey = name
            self.argument_spec[name] = spec
            self.param_key_map[spec.pop('from_result_attr', name)] = name
                
    def param(self, name, default=None):
        return self.module.params.get(name, default)

    def init_module(self):
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True,
        )

        self.host = self.param('ipa_host')
        self.port = self.param('ipa_port')
        self.protocol = self.param('ipa_prot')
        self.username = self.param('ipa_user')
        self.password = self.param('ipa_pass')
        self.headers = None
        self.state = self.param('state')
        self.changed = False


    def get_base_url(self):
        return '%s://%s/ipa' % (self.protocol, self.host)

    def get_json_url(self):
        return '%s/session/json' % self.get_base_url()

    def login(self):
        url = '%s/session/login_password' % self.get_base_url()
        data = 'user=%s&password=%s' % \
               (quote(self.username, safe=''), quote(self.password, safe=''))
        headers = {'referer': self.get_base_url(),
                   'Content-Type': 'application/x-www-form-urlencoded',
                   'Accept': 'text/plain'}
        try:
            resp, info = fetch_url(
                module=self.module, url=url,
                data=to_bytes(data), headers=headers)
            status_code = info['status']
            if status_code not in [200, 201, 204]:
                self._fail('login', info['msg'])

            self.headers = {'referer': self.get_base_url(),
                            'Content-Type': 'application/json',
                            'Accept': 'application/json',
                            'Cookie': resp.info().get('Set-Cookie')}
        except Exception:
            e = get_exception()
            self._fail('login', str(e))

    def _fail(self, msg, e):
        if 'message' in e:
            err_string = e.get('message')
        else:
            err_string = e
        self.module.fail_json(msg='%s: %s' % (msg, err_string))

    def _post_json(self, method, name, item=None, item_filter=None):
        url = '%s/session/json' % self.get_base_url()
        data = {'method': method, 'params': [name, item]}
        try:
            resp, info = fetch_url(
                module=self.module, url=url,
                data=to_bytes(json.dumps(data)), headers=self.headers)
            status_code = info['status']
            if status_code not in [200, 201, 204]:
                self._fail(method, info['msg'])
        except Exception:
            e = get_exception()
            self._fail('post %s' % method, str(e))

        if PY3:
            charset = resp.headers.get_content_charset('latin-1')
        else:
            response_charset = resp.headers.getparam('charset')
            if response_charset:
                charset = response_charset
            else:
                charset = 'latin-1'
        resp = json.loads(to_text(resp.read(), encoding=charset),
                          encoding=charset)
        err = resp.get('error')
        if err is not None:
            self._fail('response %s' % method, err)

        if 'result' in resp:
            result = resp.get('result')
            if 'result' in result:
                result = result.get('result')
                if isinstance(result, list) and \
                   method == self.methods['find'] and \
                   self.find_filter is not None:
                    result = [ i for i in result if self.find_filter(i) ]
                    return (result[-1] if len(result) > 0 else {})
            return result
        return None

    def name_map(self, action, i):
        return self._name_map.get(action, [None,{}])[i]

    def apply_value_re(self, key, val):
        filter_re = self.param_data[key]['value_filter_re']
        res = []
        for v in val:
            m = filter_re.match(val)
            if m is None:  continue
            res.append(m.group(1))
        return res

    def filter_value(self, key, val, dirty, item):
        # Subclasses may override this; return True when item was processed
        return False

    def clean(self, dirty, action='add', curr=False):
        item = {}
        name = [None, {}]
        for key, val in dirty.items():
            if not curr:
                # Special handling for request 'name' args
                if key == self.name_map(action,0): # Positional arg
                    name[0] = val
                    continue
                if key in self.name_map(action,1): # Keyword arg
                    name[1][self.name_map(action,1)[key]] = val
                    continue
            # Translate attr keys from current to change object
            if curr:  key = self.param_key_map.get(key, key)
            # All attributes in lists in find results, even scalars
            if action != 'find' and not isinstance(val, list):  val = [val]
            # Hook for special processing
            if self.filter_value(key, val, dirty, item, action):  continue
            # Ignore params not central to object definition ('dn', 'ipa_host')
            if key not in self.param_data:  continue
            # Ignore params irrelevant to this action
            if action not in self.param_data[key]['when']:  continue
            # Handle enable flag attr
            if key == self.enablekey:
                if action in ('enable','disable'):
                    item['enabled'] = val[0]
                else:  continue # Skip it
            # Munge current attr values into change-compatible values
            if curr and self.param_data[key]['value_filter_re'] is not None:
                val = self.apply_value_re(key, val)
            # Ignore empty values
            if val==[] or val[0] is None:  continue
            # Convert 'TRUE' and 'FALSE' to booleans
            if self.param_data[key]['type'] == 'bool' \
               and isinstance(val[0], basestring):
                if val[0].lower() == 'true': val[0] = True
                elif val[0].lower() == 'false': val[0] = False
            if self.param_data[key]['req_key'] is not None:
                # Add key:{__req_key__:val} to item
                item[key] = { self.param_data[key]['req_key']:val }
            else:
                # Add key:val to item
                item[key] = val
        # Most API requests don't need kw args
        if not name[1]: name.pop(1)
        return dict(
            item=item,
            name=name,
            method=self._methods[action],
        )

    def find(self):
        request = self.clean(self.module.params, 'find')
        request['item'].update(dict(all=True))
        request['item'].update(self.extra_find_args)
        self.final_obj = self.updated_obj = self.found_obj = \
                         self._post_json(**request)

    def op(self, a, b, op):
        keys = set(self.param_data.keys())
        res = {}
        for key in set(a) | set(b):
            # if key not in self.param_data: continue
            # FIXME can we treat scalars this way?
            # if self.param_data[key]['type'] != 'list': continue
            # FIXME
            # if 'add' not in self.param_data[key]['when']: continue
            # => res_val = a[key] <op> b[key]
            res_val = list(getattr(set(a.get(key, [])), op)(b.get(key, [])))
            if res_val: res.setdefault(key,[]).extend(res_val)
        return res

    def compute_changes(self):
        request = self.clean(self.module.params,
                             action = 'mod' if self.found_obj else 'add')
        change_params = request['item']
        current = self.clean(self.found_obj, curr=True,
                             action = 'mod' if self.found_obj else 'add')
        curr_params = current['item']

        changes = {'addattr':{}, 'delattr':{}, 'setattr':{}}

        # Compute changes for list parameters
        if self.state in ('exact', 'present', 'enabled', 'disabled'):
            changes['addattr'].update(
                self.op(change_params, curr_params, 'difference'))
        if self.state == 'exact':
            changes['delattr'].update(
                self.op(curr_params, change_params, 'difference'))
        if self.state == 'absent':
            changes['delattr'].update(
                self.op(change_params, curr_params, 'intersection'))

        # Compute changes for scalar parameters
        for key in changes['addattr'].keys():
            # Find only non-list keys
            if self.param_data[key]['type'] == 'list':  continue
            # Sanity check:  exactly one entry in add list
            if len(changes['addattr'][key]) != 1:
                self._fail(key, 'Found multiple entries of non-list attribute')
            # Sanity check:  no more than one entry in del list
            if len(changes['delattr'].get(key,[])) > 1:
                self._fail(key, 'Found multiple entries of non-list attribute')
            # Pop key from del list
            changes['delattr'].pop(key,None)
            # Move key from add list to set list
            changes['setattr'][key] = changes['addattr'].pop(key)

        request['item'] = changes

        # Do any last-minute request patching
        self.request_cleanup(request)

        self.changed = bool(changes['addattr'] or changes['delattr']
                            or changes['setattr'])
        return request

    def expand_changes(self, request):
        expanded_changes = {'addattr':[], 'delattr':[], 'setattr':[],
                            'all':True}
        for op in request['item']:
            for attr, val_list in request['item'][op].items():
                for val in val_list:
                    expanded_changes[op].append("%s=%s" % (attr, val))
            expanded_changes[op].sort() # Sort for unit tests
        request['item'] = expanded_changes

    def request_cleanup(self, request):
        # Subclasses may override to patch up request before posting
        pass

    def add_or_mod(self):

        # Compute list of items to modify/add/delete
        request = self.compute_changes()

        if self.module.check_mode or not self.changed:
            self.updated_obj = self.found_obj
            return
        
        self.expand_changes(request)

        self.final_obj = self.updated_obj = self._post_json(**request)

    @property
    def is_enabled(self):
        val = self.updated_obj.get(self.enablekey,[False])[0]
        if isinstance(val, basestring):
            if val.lower() == 'true': return True
            if val.lower() == 'false': return False
        return val

    def enable_or_disable(self):
        # Do nothing if state is present/exact/absent
        if self.state not in ('disabled','enabled'):  return

        # Do nothing if state is already correct
        if (self.state == 'enabled' and self.is_enabled) \
           or (self.state == 'disabled' and not self.is_enabled):
            return

        # Mark task as changed
        self.changed = True

        # Do nothing in check mode
        if self.module.check_mode: return

        # Effect requested state
        request = self.clean(self.module.params, action=self.state)
        self.final_obj = self._post_json(**request)
        
    def rem(self):
        if self.module.check_mode: return

        request = self.clean(self.module.params, 'rem')
        self.final_obj = self.updated_obj = self._post_json(**request)

    def ensure(self):

        # Find any existing objects
        self.find()

        if self.state == 'absent':
            if not self.found_obj:
                # Object is already absent; do nothing
                return False, {}

            # If no parameters in request, then 'absent' means to
            # remove the entire object here
            if not self.clean(self.module.params, 'mod')['item']:
                # No keys in request:  remove whole object
                self.rem()
                return True, {}
            # Otherwise, 'absent' means to remove items from list keys

        # Effect changes
        self.add_or_mod()
        self.enable_or_disable()

        return self.changed, self.final_obj

    def main(self):

        try:
            self.login()
            changed, obj = self.ensure()
            result = {
                'changed': changed,
                self.name: obj,
            }
            self.module.exit_json(**result)
        except Exception:
            e = get_exception()
            self.module.fail_json(msg=str(e))

