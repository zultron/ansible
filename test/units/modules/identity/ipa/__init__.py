# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import call, create_autospec, patch, MagicMock

from copy import deepcopy
from pprint import pprint

class AbstractTestClass(object):

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
                      found_obj={},
                      side_effect=None):
        # Mock AnsibleModule instance with attributes
        mod = mod_cls.return_value
        mod.check_mode = False
        # Set up module params for test
        mod.params = module_params.copy() or self.module_params.copy()
        mod.params.update(module_params_updates)
        # Set up fail_json() method
        def raise_exception(msg):  raise RuntimeError(msg)
        mod.fail_json = MagicMock(side_effect=raise_exception)

        # Create instance
        client = self.test_class()

        # Check that AnsibleModule class was correctly patched
        assert client.module is mod

        # Patch _post_json method (object only, not class)
        if side_effect is not None:
            self.mock_post_json = MagicMock(side_effect=side_effect)
        else:
            self.mock_post_json = MagicMock(return_value=found_obj)
        client._post_json = self.mock_post_json

        return client

    #################################################################
    # init()
    #################################################################

    def test_01_init(self):
        # Test module's basic consistency; instance doesn't matter
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

    def runner(self, module_params = None, post_json_calls=None):
        #
        # Set up patched test object
        #

        # - Pre-ordained set of replies from _post_json()
        reply_list = []
        for c in post_json_calls:
            # Recycle previous reply if no new one given
            reply = deepcopy(c.get('reply',([None]+reply_list)[-1]))
            reply.update(deepcopy(c.get('reply_updates',{})))
            reply_list.append(reply)
        # - Patched test class instance
        client1 = self.get_tst_class(
            module_params = deepcopy(module_params),
            side_effect = deepcopy(reply_list))

        #
        # Run ensure()
        #
        client1.ensure()

        #
        # Verify run
        #
        print "Number of calls: %d" % client1._post_json.call_count
        for request, call, reply in \
            zip(client1._post_json.call_args_list, post_json_calls, reply_list):
            print "\n*** Request:  %s" % call['name']
            print "--- Sent:"
            pprint(request[1])
            print "--- Expected:"
            pprint(call['request'])
            print "--- Reply:"
            pprint(reply)

        # - Number of calls to _post_json
        self.assertEqual(client1._post_json.call_count, len(post_json_calls))

        # - Call parameters
        for request, call in \
            zip(client1._post_json.call_args_list, post_json_calls):
            self.assertEqual(request[1],call['request'])

        # - DN of found object
        if 'dn' in reply_list[0]:
            self.assertEqual(reply_list[0]['dn'],
                             client1.found_obj.get('dn',None))

        ###################################
        # Idempotency
        #

        #
        # Set up 2nd patched test object
        #

        # - Copy final result from previous object
        found_obj = deepcopy(client1.final_obj)
        # found_obj.update(deepcopy(idempotency.get('obj_updates',{})))
        # - Patched test class instance
        client2 = self.get_tst_class(
            module_params = deepcopy(module_params),
            side_effect = [found_obj])

        #
        # Run ensure()
        #
        client2.ensure()

        #
        # Run and verify add_or_mod()
        #

        # Verify ONLY the find call happened (or print debug info & fail)
        print "*** Idempotency:"
        print "--- Current result:"
        pprint(client2.final_obj)
        if client2._post_json.call_count != 1:
            for request, call in \
                zip(client2._post_json.call_args_list, post_json_calls):
                print "--- Sent request:"
                pprint(request[1])
                print "--- Expected request:"
                pprint(call['request'])
            print "\n*** Idempotency error"
        self.assertEqual(client2._post_json.call_count, 1)
        print "\n*** SUCCESS"

        return client1
