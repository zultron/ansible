# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import call, create_autospec, patch, MagicMock

from copy import deepcopy
from pprint import pprint

class AbstractTestClass(unittest.TestCase):

    # test_class = SomeNameIPAClient
    test_class = None

    # Module parameters as supplied in task
    module_params = dict(
        # param1 = "val1",
        # state = "enabled",
        # ipa_host = "host1.example.com",
        # ipa_user = "admin",
        # ipa_pass = "secretpass",
    )



    @patch('ansible.module_utils.ipa.AnsibleModule', autospec=True)
    def get_tst_class(self, mod_cls,
                      module_params={},
                      module_params_updates={},
                      found_obj=None):
        # Mock AnsibleModule instance with attributes
        mod = mod_cls.return_value
        mod.check_mode = False
        # Set up module params for test
        mod.params = module_params.copy() or self.module_params.copy()
        mod.params.update(module_params_updates)

        # Create instance
        client = self.test_class()

        # Check that AnsibleModule class was correctly patched
        assert client.module is mod

        # Patch _post_json method (object only, not class)
        if found_obj is None:  found_obj = self.found_obj
        self.mock_post_json = MagicMock(return_value=found_obj)
        client._post_json = self.mock_post_json

        return client

    #################################################################
    # init()
    #################################################################

    def test_01_init(self):
        client = self.get_tst_class()

        # Verify client._methods keys
        self.assertEqual(set(self.test_class.methods.keys()),
                         set(client._methods.keys()))

        # Verify argument_spec keys
        self.assertEqual(
            set(['state','ipa_prot','ipa_host','ipa_port',
                 'ipa_user','ipa_pass','validate_certs']) |
            set(client.kw_args.keys()),
            set(client.argument_spec.keys()))

        # Check for known NAME key in action types
        for action_type in ['add','rem']:
            self.assertIsInstance(client.name_map(action_type,0), basestring)

        # Enable/disable checks
        if 'enabled' in client._methods or 'disabled' in client._methods:
            # The complement must also exist
            self.assertIn('enabled', client._methods)
            self.assertIn('disabled', client._methods)
            # And the flag param must be specified
            self.assertIsNotNone(client.enablekey)
        else: # The opposite:
            # The complement must not exist
            self.assertNotIn('enabled', client._methods)
            self.assertNotIn('disabled', client._methods)
            # And the flag param must not be specified
            self.assertIsNone(client.enablekey)


    #################################################################
    # find()
    #################################################################

    # Parameters expected for a `find` API request
    find_params = dict(
        # method = 'somename_find',
        # name = None,
        # item = dict( all = True, param1 = 'val1' ),
        # item_filter = None,
    )

    # Sample results from a `find` API request
    found_obj = dict(
        # dn = "cn=host1.example.com.,cn=dns,dc=example,dc=com",
        # param1 = [ "val1" ], 
        # objectclass = [ "someclass1", "top", "someclass2" ],
    )


    def test_02_find(self):
        client = self.get_tst_class()

        # Exercise find()
        client.find()

        # Verify the call
        self.assertEqual(client._post_json.call_count, 1)
        print "--- call_args:"
        pprint (client._post_json.call_args[1])
        self.assertEqual(client._post_json.call_args,
                         call(**self.find_params))

        # Verify the result
        print "client.found_obj:"; pprint (client.found_obj)
        self.assertEqual(self.found_obj['dn'], client.found_obj['dn'])


    #################################################################
    # add_or_mod()
    #################################################################

    def add_or_mod_helper(self, test_data_attr):
        test_data = deepcopy(getattr(self, test_data_attr))
        if isinstance(test_data, basestring):
            raise unittest.SkipTest(test_data)


        #
        # Set up patched test object
        #

        # Module params, i.e. task params
        module_params = test_data.get('module_params',self.module_params).copy()
        module_params.update(test_data.get('module_params_updates',{}))
        # Mocked output of `objtype_find()` API call
        found_obj = deepcopy(test_data.get('found_obj',{}))
        found_obj.update(test_data.get('found_obj_updates',{}))
        # Get patched test class instance
        client = self.get_tst_class(
            module_params = module_params,
            found_obj = found_obj)

        #
        # Run find()
        #

        client.find()
        print "*** find() found_obj:"; pprint(client.found_obj)
        # Sanity check: verify expected state
        self.assertEqual(module_params['state'], client.state)
        # Sanity check: found object
        if 'dn' in test_data.get('found_obj',{}):
            self.assertEqual(test_data['found_obj']['dn'],
                             client.found_obj.get('dn',None))

        #
        # Run and verify add_or_mod()
        #

        # Reset mock object
        self.mock_post_json.reset_mock()
        # Set add/mod API call mock return value
        updated_obj = deepcopy(test_data.get('updated_obj',found_obj))
        updated_obj.update(test_data.get('updated_obj_updates',{}))
        self.mock_post_json.return_value = updated_obj

        # Exercise add_or_mod()
        client.add_or_mod()

        # Verify the call happened...
        self.assertEqual(client._post_json.call_count, 1)
        print "*** add_or_mod() call_args:"
        pprint (client._post_json.call_args[1])
        self.maxDiff = None
        self.assertEqual(test_data['aom_params'],
                         client._post_json.call_args[1])
        print "*** add_or_mod() updated_obj:"; pprint(client.updated_obj)

        #
        # enable_or_disable()
        #
        eod_should_run = (
            'eod_params' in test_data or \
            (module_params['state'] == 'disabled' and client.is_enabled) or \
            (module_params['state'] == 'enabled' and not client.is_enabled))
        print '*** enable_or_disable():' \
            '  eod_should_run=%s; have eod_params=%s' % \
            (eod_should_run, 'eod_params' in test_data)

        # Reset mock object
        self.mock_post_json.reset_mock()
        # Set enable/disable API call mock return value
        final_obj = deepcopy(test_data.get('final_obj', updated_obj))
        final_obj.update(test_data.get('final_obj_updates',{}))
        self.mock_post_json.return_value = final_obj
        # Run enable_or_disable()
        client.enable_or_disable()

        # Verify the call happened if it should have
        self.assertEqual(client._post_json.call_count,
                         1 if eod_should_run else 0)

        if eod_should_run:
            print "*** enable_or_disable() call_args:"
            pprint (client._post_json.call_args[1])

            # Verify eod() API request
            if 'eod_params' in test_data:
                self.assertEqual(test_data['eod_params'],
                                 client._post_json.call_args[1])

        # Return client for idempotent run
        return client
        
    def idempotency_helper(self, old_client, test_data_attr):
        if not hasattr(self, test_data_attr):
            return
        test_data = getattr(self, test_data_attr)

        #
        # Set up patched test object
        #

        # Module params, i.e. task params
        module_params = test_data.get('module_params',self.module_params).copy()
        module_params.update(test_data.get('module_params_updates',{}))
        # Mocked output of `objtype_find()` API call
        found_obj = deepcopy(
            test_data.get('idempotent_obj',old_client.final_obj))
        found_obj.update(test_data.get('idempotent_obj_updates',{}))
        # Get patched test class instance
        new_client = self.get_tst_class(
            module_params = module_params,
            found_obj = found_obj)
        # Run find()
        new_client.find()

        #
        # Run and verify add_or_mod()
        #

        # Reset mock object
        self.mock_post_json.reset_mock()
        # Set add/mod API call mock return value
        self.mock_post_json.return_value = deepcopy(found_obj)
        # Exercise add_or_mod()
        new_client.add_or_mod()
        # Verify the call did NOT happen (or print debug info & fail)
        if new_client._post_json.call_count > 0:
            print "*** idempotency error:  add_or_mod()"
            print "--- module_params:"
            pprint (module_params)
            print "--- found_obj:"
            pprint (new_client.found_obj)
            print "--- call_args:"
            pprint (new_client._post_json.call_args[1])
        self.assertEqual(new_client._post_json.call_count, 0)
        print "*** Idempotency add_or_mod():  success"

        #
        # Run and verify enable_or_disable()
        #

        # Reset mock object
        self.mock_post_json.reset_mock()
        # Set enable/disable API call mock return value
        self.mock_post_json.return_value = deepcopy(found_obj)
        # Run enable_or_disable()
        new_client.enable_or_disable()
        # Verify the call did NOT happen
        if new_client._post_json.call_count > 0:
            print "*** idempotency error:  enable_or_disable()"
            print "--- module_params:"
            pprint (module_params)
            print "--- found_obj:"
            pprint (found_obj)
            print "--- call_args:"
            pprint (new_client._post_json.call_args[1])
        self.assertEqual(new_client._post_json.call_count, 0)
        print "*** Idempotency enable_or_disable():  success"

    def test_04_present_existing(self):
        # Test state==present on existing object
        # present_existing_data = {
        #     'found_obj' : found_obj,
        #     'aom_params' : {
        #         'item' : {'all': True,
        #                   'addattr': [...],  # Add items here or
        #                   'setattr': [...],  # here as appropriate
        #                   'delattr': []},    # Leave this empty
        #         'item_filter': None,
        #         'method' : 'objtype_mod',
        #         'name' : ['myobject_key']},
        # }
        client = self.add_or_mod_helper('present_existing_data')
        self.idempotency_helper(client, 'present_existing_data')

    def test_05_enabled_existing(self):
        # Test state==enabled on existing object
        # enabled_existing_data = {
        #     'module_params_updates' : {'state' : 'enabled'},
        #     'found_obj' : found_obj,
        #     'aom_params' : { (like 'present_existing' test) },
        #     # Set up so `objtype_enable` method runs...
        #     'found_obj_updates' : {'objtypeactive' : ['FALSE']},
        #     # ...and verify enable/disable API call params
        #     'eod_params' : {
        #         'item' : {},
        #         'item_filter': None,
        #         'method' : 'dnszone_enable',
        #         'name' : ['test.example.com']},
        # }
        client = self.add_or_mod_helper('enabled_existing_data')
        self.idempotency_helper(client, 'enabled_existing_data')

    def test_06_present_new(self):
        # Test state==present on new object
        # present_new_data = {
        #     'found_obj' : {},
        #     'aom_params' : {
        #          (like 'present_existing' test, but different method)
        #         'method' : 'objtype_add'},
        # }
        client = self.add_or_mod_helper('present_new_data')
        self.idempotency_helper(client, 'present_new_data')

    def test_07_disabled_new(self):
        # Test state==disabled on new object
        # present_new_data = {
        #     'found_obj' : {},
        #     'aom_params' : {
        #          (like 'present_existing' test, but different method)
        #         'method' : 'objtype_add'},
        #     # Set up so `objtype_disable` method runs...
        #     'found_obj_updates' : {'objtypeactive' : ['TRUE']},
        #     # ...and verify enable/disable API call params
        #     'eod_params' : {
        #         'item' : {},
        #         'item_filter': None,
        #         'method' : 'dnszone_disable',
        #         'name' : ['test.example.com']},
        # }
        client = self.add_or_mod_helper('disabled_new_data')
        self.idempotency_helper(client, 'disabled_new_data')

    def test_08_exact_existing(self):
        # Test state==exact on existing object
        # present_existing_data = {
        #     'found_obj' : found_obj,
        #     'aom_params' : {
        #         'item' : {'all': True,
        #                   'addattr': [...],  # Add items to any
        #                   'setattr': [...],  # of these, as appropriate
        #                   'delattr': [...]},
        #         'item_filter': None,
        #         'method' : 'objtype_mod',
        #         'name' : ['myobject_key']},
        # }
        client = self.add_or_mod_helper('exact_existing_data')
        self.idempotency_helper(client, 'exact_existing_data')

    def test_20_rem(self):
        client = self.get_tst_class(
            module_params_updates=dict(state='absent'))
        client.find()
        self.mock_post_json.reset_mock()

        # Exercise rem()
        client.rem()

        # Verify the call
        self.assertEqual(client._post_json.call_count, 1)
        print "client._post_json.call_args:"
        pprint (client._post_json.call_args[1])
        self.assertEqual(self.rem_params, client._post_json.call_args[1])

