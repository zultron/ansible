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
    # runner()
    #################################################################

    # Track state from test to test
    current_state = {}

    @property
    def previous_client(self):
        previous_test_key = self.test_key - 1
        if previous_test_key not in self.current_state:
            raise unittest.SkipTest(
                'Client for test index %d not available' % previous_test_key)
        return self.current_state[previous_test_key]['client']

    def persist_client(self, client):
        self.current_state.setdefault(self.test_key,{})['client'] = client

    def runner(self, test_key, module_params = None, post_json_calls=None):
        # test_key is an integer used to persist data between tests,
        # guaranteeing order
        self.test_key = test_key

        #
        # Set up reply list
        #

        # - Pre-ordained set of replies from _post_json()
        reply_list = []
        for i, c in enumerate(post_json_calls):
            if 'reply' not in c:
                # Generate 'reply' key/value when not supplied
                if i == 0:
                    # For initial find() request, use the previous
                    # client final_obj
                    reply = deepcopy(self.previous_client.final_obj)
                else:
                    # For later requests, recycle the previous reply
                    reply = deepcopy(reply_list[-1])
            else:
                reply = c['reply']
            # Apply any updates
            reply.update(deepcopy(c.get('reply_updates',{})))
            # Save reply for next round
            reply_list.append(reply)

        #
        # Set up patched test object
        #

        # - Patched test class instance
        client1 = self.get_tst_class(
            module_params = deepcopy(module_params),
            side_effect = deepcopy(reply_list))
        # - Save instance for later tests
        self.persist_client(client1)

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

        # - find() call parameters
        self.assertEqual(post_json_calls[0]['request'],
                         client1._post_json.call_args_list[0][1])

        # - Number of calls to _post_json
        self.assertEqual(client1._post_json.call_count, len(post_json_calls))

        # - Following call parameters
        for request, call in \
            zip(client1._post_json.call_args_list[1:], post_json_calls[1:]):
            self.assertEqual(call['request'],request[1])

        # - DN of found object
        if 'dn' in reply_list[0]:
            self.assertEqual(reply_list[0]['dn'],
                             client1.found_obj.get('dn',None))

        ###################################
        # Idempotency
        #
        print "*** Idempotency:"

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
        try:
            client2.ensure()
            raised_exception = False
        except:
            # Defer raising exception until after printing debug info
            raised_exception = True

        #
        # Run and verify add_or_mod()
        #

        # Verify ONLY the find call happened (or print debug info & fail)
        for request, call in \
            zip(client2._post_json.call_args_list, post_json_calls):
            print "--- Sent request:"
            pprint(request[1])
            print "--- Expected request:"
            pprint(call['request'])
        if client2._post_json.call_count > 1:
            try:
                print "--- Cleaned module params:"
                pprint(client2.change_params)
                print "--- Cleaned find reply params:"
                pprint(client2.curr_params)
            except: pass
        print "--- Got result:"
        pprint(client2.final_obj)

        # Raise any earlier exception
        if raised_exception:  raise

        if raised_exception or client2._post_json.call_count != 1:
            print "\n*** Idempotency error"
        self.assertEqual(client2._post_json.call_count, 1)
        print "\n*** SUCCESS"


