# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import call, create_autospec, patch, MagicMock

from copy import deepcopy
from pprint import pprint
import os

class IPATestError(RuntimeError):
    pass

class AbstractTestClass(object):

    # test_class = SomeNameIPAClient
    test_class = None

    live_host = os.getenv('IPA_HOST', False)

    ipa_domain = os.getenv('IPA_DOMAIN', 'example.com')

    ipa_host = os.getenv('IPA_HOST','host1.example.com')
    ipa_user = os.getenv('IPA_USER','admin')
    ipa_pass = os.getenv('IPA_PASS','secretpass')

    @classmethod
    @patch('ansible.module_utils.ipa.AnsibleModule', autospec=True)
    def get_tst_class(cls, mod_cls,
                      module_params={},
                      reply_list=[],
                      live_host_ok=True):

        live_host = cls.live_host and live_host_ok

        # Init reply_list
        if live_host:
            reply_list = []
        else:
            reply_list = reply_list

        # Mock AnsibleModule instance
        mod = mod_cls.return_value
        # Turn off check mode
        mod.check_mode = False
        # Add module params
        mod.params = module_params.copy()
        mod.params.update(dict(
            ipa_host = cls.ipa_host,
            ipa_user = cls.ipa_user,
            ipa_pass = cls.ipa_pass))
        mod.params['ipa_prot'] = 'https'
        # The fail_json() method must raise an exception
        def raise_exception(msg, **kwargs):  raise IPATestError(msg, kwargs)
        mod.fail_json = MagicMock(side_effect=raise_exception)

        # Create test class instance
        client = cls.test_class()
        if live_host:
            client.login()

        # Check that AnsibleModule class was correctly patched
        assert client.module is mod

        # Patch _post_json() method (patch instance, not class)
        if live_host:
            # Run the real _post_json() via Mock so we can examine
            # calls
            pj = client._post_json
            def _post_json_wrapper(*args, **kwargs):
                reply = pj(*args, **kwargs)
                reply_list.append(reply)
                return reply
            mock_post_json = MagicMock(
                side_effect=_post_json_wrapper)
        else:
            mock_post_json = MagicMock(
                side_effect=reply_list)
            # Make exists() property work correctly despite mocked _post_json()
            if reply_list:
                client.responses[client._methods['find']] = {
                    'result':{'count': (1 if reply_list[0] else 0)}}
        client._post_json = mock_post_json

        return client

    #################################################################
    # init()
    #################################################################

    def test_01_init(self):
        # Test module's basic consistency; instance doesn't matter
        client = self.get_tst_class(
            live_host_ok=False)
        self.client = client

        # Verify client._methods keys
        self.assertEqual(set(self.test_class.methods.keys()),
                         set(client._methods.keys()))

        # Verify argument_spec keys
        self.assertEqual(
            set(['state','ipa_prot','ipa_host','ipa_port',
                 'ipa_user','ipa_pass','validate_certs']) |
            set(client.kw_args.keys()),
            set(client.argument_spec.keys()))

        # Verify base_keys is a set
        self.assertIsInstance(client.base_keys, set)

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
        if not self.live_host:
            for i, c in enumerate(post_json_calls):
                if 'reply' not in c:
                    # Generate 'reply' key/value when not supplied
                    if i == 0:
                        # For initial find() request, use the previous
                        # client final_obj
                        reply = deepcopy(
                            self.previous_client.requests[-1]['response'])
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
            reply_list = deepcopy(reply_list))

        #
        # Run ensure()
        #
        try:
            client1.ensure()
            raised_exception = False
        except Exception as e:
            # Defer raising exception until after printing debug info
            print "Exception raised while running client1.ensure():"
            print e
            raised_exception = True

        #
        # Print a lot of debug data
        #
        print "Number of calls: %d; expected: %d" % (
            client1._post_json.call_count, len(post_json_calls))
        print "\n*** Module params: ***"
        pprint(client1.module.params)
        print "\n*** Module canonical params, state=%s: ***" % client1.state
        pprint(getattr(client1,'canon_params',
                       '   canon_params not initialized'))
        print "\n*** Cleaned response: ***"
        pprint(getattr(client1,'response_cleaned','(No response_cleaned attr)'))
        for i in range(client1._post_json.call_count):
            if client1._post_json.call_count > i:
                try:
                    print "\n*** Call #%d:  %s (%s) ***" % \
                        (i,
                         (post_json_calls[i]['name'] if i < len(post_json_calls)
                          else 'EXTRA CALL'),
                         client1.requests[i]['name'])
                    if i > 1 and \
                       client1._post_json.call_args_list[i][1]['method'] in (
                           client1._methods['add'], client1._methods['mod']):
                        print "--- Cleaned find response params:"
                        pprint(client1.curr_params)
                    print "--- Request #%d:" % i
                    pprint(client1._post_json.call_args_list[i][1])
                    if i < len(post_json_calls):
                        print "--- Expected request #%d:" % i
                        pprint(post_json_calls[i]['request'])
                    else:
                        print "--- UNEXPECTED request #%d" % i
                    print "--- Response:"
                    pprint(client1.requests[i].get('response','NO RESPONSE'))
                    if i == 0:
                        print "--- Cleaned module params:"
                        pprint(client1.canon_params)
                        print "--- Diffs:"
                        pprint(getattr(client1,'diffs','diffs not available'))
                except Exception as e_print:
                    print "Exception raised while printing debug info:"
                    print e_print
                    break

        #
        # Verify run
        #

        # Raise any earlier exception
        if raised_exception:  raise

        # - find() call parameters
        find_req_expected = post_json_calls[0]['request']
        find_req_actual = client1._post_json.call_args_list[0][1]
        self.assertEqual(find_req_expected, find_req_actual)

        # - Number of calls to _post_json
        post_json_calls_expected = client1._post_json.call_count
        post_json_calls_actual = len(post_json_calls)
        self.assertEqual(post_json_calls_expected, post_json_calls_actual)

        # - Following call parameters
        for request_actual, request_expected in \
            zip([l[1] for l in client1._post_json.call_args_list[1:]],
                [l['request'] for l in post_json_calls[1:]]):
            self.assertEqual(request_expected,request_actual)

        # - Changed
        if getattr(self,"test_changed",True) is True:
            self.assertTrue(client1.changed)
        else:
            self.assertFalse(client1.changed)

        # - Save instance for later tests
        self.persist_client(client1)

        ###################################
        # Idempotency
        #
        print "*** Idempotency:"

        #
        # Set up 2nd patched test object
        #

        # - Copy final result from previous object
        found_obj = deepcopy(client1.requests[-1]['response'])
        # found_obj.update(deepcopy(idempotency.get('obj_updates',{})))
        # - Patched test class instance
        client2 = self.get_tst_class(
            module_params = deepcopy(module_params),
            reply_list = [deepcopy(found_obj)])

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
        # Print a lot of debug data
        #

        # Verify ONLY the find call happened (or print debug info & fail)
        print "--- Sent find() request:"
        pprint(client2._post_json.call_args_list[0][1])
        print "--- Expected find() request:"
        pprint(post_json_calls[0]['request'])
        print "--- Response:"
        pprint(client2.requests[0]['response'])
        print "--- Response cleaned:"
        pprint(client2.requests[0].get(
            'response_cleaned','(No response_cleaned key)'))
        print "--- Cleaned module params:"
        pprint(client1.canon_params)
        print "--- Diffs:"
        pprint(getattr(client2,'diffs','diffs not available'))
        if client2._post_json.call_count > 1:
            try:
                print "--- Second request:"
                pprint(client2.requests[1])
            except: pass

        #
        # Verify
        #

        # Raise any earlier exception
        if raised_exception:  raise

        # - Changed
        self.assertFalse(client2.changed)

        if raised_exception or client2._post_json.call_count != 1:
            print "\n*** Idempotency error"
        self.assertEqual(client2._post_json.call_count, 1)
        print "\n*** SUCCESS"

        return client1

class AbstractEnablableTestClass(AbstractTestClass):

    def test_01_init(self):
        super(AbstractEnablableTestClass, self).test_01_init()
        client = self.client

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
