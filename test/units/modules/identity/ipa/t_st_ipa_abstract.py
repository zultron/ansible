# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import call, create_autospec, patch, MagicMock

from pprint import pprint

class AbstractTestClass(unittest.TestCase):

    # test_class = SomeNameIPAClient
    test_class = None
    # ipa_module = 'ipa_somename'
    ipa_module = None

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
                      module_params_updates={},
                      find_result=None):
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
        if find_result is None:  find_result = self.find_result
        self.mock_post_json = MagicMock(return_value=find_result)
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

        # Exercise find()
        client.find()

        # Verify the call
        self.assertEqual(client._post_json.call_count, 1)
        self.assertEqual(client._post_json.call_args,
                         call(**self.find_params))

        # Verify the result
        print "client.current_obj:"; pprint (client.current_obj)

        self.assertEqual(self.find_result['dn'], client.current_obj['dn'])


    #################################################################
    # compute_changes()
    #################################################################

    def test_03_compute_changes(self):
        client = self.get_tst_class(
            find_result=self.find_result)
        client.find()

        # Exercise compute_changes()
        request = client.compute_changes()

        # Verify changes
        print "client.changes:"; pprint (client.changes)
        self.assertEqual(self.compute_changes_results, client.changes)

    #################################################################
    # add_or_mod()
    #################################################################

    def add_or_mod_helper(
            self,
            expected_result_attr=None,
            find_result={},
            expected_state=None,
            module_params_updates={} ):
        if not hasattr(self, expected_result_attr):
            return unittest.skip('Unimplemented or inapplicable')
        expected_result = getattr(self, expected_result_attr)

        # Get patched test class
        client = self.get_tst_class(
            find_result=find_result,
            module_params_updates=module_params_updates)
        # Run find():  set up for add_or_mod
        client.find()
        # Sanity check: verify expected state
        self.assertEqual(expected_state, client.state)
        # Reset mock object
        self.mock_post_json.reset_mock()

        # Exercise add_or_mod()
        client.add_or_mod()

        # Verify the call
        self.assertEqual(client._post_json.call_count, 1)
        print "client._post_json.call_args:"
        pprint (client._post_json.call_args[1])
        self.assertEqual(expected_result, client._post_json.call_args[1])

    def test_04_present_existing(self):
        self.add_or_mod_helper(
            'present_existing_params',
            expected_state='present',
            find_result=self.find_result)

    def test_05_enabled_existing(self):
        self.add_or_mod_helper(
            'enabled_existing_params',
            expected_state='enabled',
            find_result=self.find_result)

    def test_06_present_new(self):
        self.add_or_mod_helper(
            'present_new_params',
            expected_state='present')

    def test_07_disabled_new(self):
        self.add_or_mod_helper(
            'disabled_new_params',
            expected_state='disabled',
            module_params_updates={'state':'disabled'})

    def test_08_exact_existing(self):
        self.maxDiff=None
        self.add_or_mod_helper(
            'exact_existing_params',
            expected_state='exact',
            find_result=self.find_result,
            module_params_updates={'state':'exact'})

    def test_09_rem(self):
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
