# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import call, create_autospec, patch, MagicMock

from ansible.module_utils.ipa import IPAObjectDiff

class AbstractTestClass(unittest.TestCase):

    # test_class = SomeNameIPAClient
    test_class = None
    # ipa_module = 'ipa_somename'
    ipa_module = None
    test_diff_class = IPAObjectDiff

    # Module parameters as supplied in task
    module_params = dict(
        # param1 = "val1",
        # state = "enabled",
        # ipa_host = "host1.example.com",
        # ipa_user = "admin",
        # ipa_pass = "secretpass",
    )



    @patch('ansible.module_utils.ipa.AnsibleModule', autospec=True)
    def get_tst_class(self, mod_cls, module_params_updates={}):
        # Mock AnsibleModule instance with attributes
        mod = mod_cls.return_value
        mod.check_mode = False
        # Update module params for test
        mod.params = self.module_params.copy()
        mod.params.update(module_params_updates)

        # Create instance
        client = self.test_class()

        # Check that AnsibleModule class was correctly patched
        assert client.module is mod

        # Patch _post_json method (object only, not class)
        client._post_json = MagicMock(return_value=self.find_result)

        return client

    #################################################################
    # init()
    #################################################################

    def test_01_init(self):
        client = self.get_tst_class()

        # Verify client._methods keys
        self.assertEqual(set(client._methods.keys()),
                         set(self.test_class.methods.keys()))

        # Verify argument_spec keys
        self.assertEqual(
            set(['state','ipa_prot','ipa_host','ipa_port',
                 'ipa_user','ipa_pass','validate_certs']) |
            set(client.kw_args.keys()),
            set(client.argument_spec.keys()))

        # Check for known NAME key in action types
        for action_type in ['add','rem','mod']:
            self.assertIn(action_type, client.name_map)

        # Enable/disable checks
        if 'enable' in client._methods or 'disable' in client._methods:
            # The complement must also exist
            self.assertIn('enable', client._methods)
            self.assertIn('disable', client._methods)
            # And the flag param must be specified
            self.assertIsNotNone(client.enablekey)
        else: # The opposite:
            # The complement must not exist
            self.assertNotIn('enable', client._methods)
            self.assertNotIn('disable', client._methods)
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
    find_result = dict(
        # dn = "cn=host1.example.com.,cn=dns,dc=example,dc=com",
        # param1 = [ "val1" ], 
        # objectclass = [ "someclass1", "top", "someclass2" ],
    )


    def test_02_find(self):
        client = self.get_tst_class()

        # Verify action_type
        self.assertEqual(client.action_type, 'find')

        # Exercise find()
        client.find()

        # Verify the call
        self.assertEqual(client._post_json.call_count, 1)
        self.assertEqual(client._post_json.call_args,
                         call(**self.find_params))

        # Verify the result
        self.assertEqual(client.new_obj['dn'], self.find_result['dn'])

    #################################################################
    # diff class
    #################################################################

    def test_03_diff(self):
        client = self.get_tst_class()

        # Create diff object
        diff = self.test_diff_class(
            self.find_result, client.module.params, client.method_map,
            client.method_trans, 'rem')

        # Check clean() method results
        self.assertEqual(diff.curr, self.curr_cleaned)
        self.assertEqual(diff.change, self.change_cleaned)
        
        # Check present(), exact(), absent() method results
        for state in self.diff_results:
            for action_type, result in self.diff_results[state].items():
                diff.action_type = action_type
                print "state=%s; action_type=%s; changes=%s" % \
                    (state, action_type, diff.state(state))
                self.assertEqual(diff.state(state), result)

    #################################################################
    # add_or_mod()
    #################################################################

    def test_04_mod(self):
        client = self.get_tst_class()
        # Add mock `find()` results
        client.current_obj = self.find_result

        # Verify action_type
        self.assertEqual(client.action_type, 'mod')

        # Exercise add_or_mod()
        client.add_or_mod(self.diff_results['present']['mod'][0])

        # Verify the call
        self.assertEqual(client._post_json.call_count, 1)
        self.assertEqual(client._post_json.call_args,
                         call(**self.mod_params))

    def test_05_add(self):
        client = self.get_tst_class()
        # Add empty mock `find()` results
        client.current_obj = {}

        # Verify action_type
        self.assertEqual(client.action_type, 'add')

        # Exercise add_or_mod()
        client.add_or_mod(self.diff_results['present']['add'][0])

        # Verify the call
        self.assertEqual(client._post_json.call_count, 1)
        self.assertEqual(client._post_json.call_args,
                         call(**self.add_params))

    def test_06_rem(self):
        client = self.get_tst_class(
            module_params_updates=dict(state='absent'))
        # Add mock `find()` results
        client.current_obj = self.find_result

        # Verify action_type
        self.assertEqual(client.action_type, 'rem')

        # Exercise rem()
        client.rem()

        # Verify the call
        self.assertEqual(client._post_json.call_count, 1)
        self.assertEqual(client._post_json.call_args,
                         call(**self.rem_params))
