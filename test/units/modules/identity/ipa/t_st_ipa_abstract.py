# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import call, create_autospec, patch

class AbstractTestClass(unittest.TestCase):

    # test_class = SomeNameIPAClient
    test_class = None
    # ipa_module = 'ipa_somename'
    ipa_module = None

    # Module parameters as supplied in task
    mod_params = dict(
        # param1 = "val1",
        # state = "enabled",
        # ipa_host = "host1.example.com",
        # ipa_user = "admin",
        # ipa_pass = "secretpass",
    )

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


    @patch('ansible.module_utils.ipa.IPAClient._post_json')
    @patch('ansible.module_utils.ipa.AnsibleModule', autospec=True)
    def test__find(self, mod_cls, pj):
        # Mock AnsibleModule instance with `params` dict
        mod = mod_cls.return_value
        mod.params = self.mod_params

        # Mock _post_json return value
        pj.return_value = self.find_result

        # Exercise find()
        client = self.test_class()
        client.find()

        # Verify the call
        self.assertEqual(1, pj.call_count)
        self.assertEqual(call(**self.find_params), pj.call_args)

        # Verify the result
        self.assertEqual(client.new_obj['dn'], self.find_result['dn'])
