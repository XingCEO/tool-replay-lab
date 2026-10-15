import unittest
from tool_replay_lab import analyze

class ReplayTests(unittest.TestCase):
    def test_insert_does_not_cascade(self):
        a={'tool':'a'}; b={'tool':'b'}
        r=analyze({'expected':[a,b],'observed':[a,{'tool':'x'},b]})
        self.assertEqual([x['kind'] for x in r['changes']],['insert'])
    def test_ignore_keeps_original(self):
        c={'tool':'x','result':{'id':1}}
        self.assertTrue(analyze({'expected':[c],'observed':[{'tool':'x','result':{'id':2}}],'ignore':['/result/id']})['matches'])
        self.assertEqual(c['result']['id'],1)
    def test_escaped_pointer(self):
        r=analyze({'expected':[{'tool':'x','result':{'a/b':1}}],'observed':[{'tool':'x','result':{'a/b':2}}],'ignore':['/result/a~1b']})
        self.assertTrue(r['matches'])
    def test_error_is_compared(self):
        self.assertFalse(analyze({'expected':[{'tool':'x','error':'timeout'}],'observed':[{'tool':'x','result':1}]})['matches'])
    def test_invalid_pointer(self):
        with self.assertRaises(ValueError): analyze({'expected':[{'tool':'x'}],'observed':[],'ignore':['bad']})
