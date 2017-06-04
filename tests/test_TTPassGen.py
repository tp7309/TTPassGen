#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function
import unittest, os
from ttpassgen import ttpassgen

#test/in.dict generate by: ttpassgen.py -r [123]{3:3} in.dict
class Test_ttpassgen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(Test_ttpassgen, cls).setUpClass()
        def lc_func():
            if not os.path.exists('testout.dict'): return 0
            with open('testout.dict', 'r') as f:
                return len(f.readlines())
        global lc
        lc = lc_func

        def go_func(rule, dictlist='tests/in.dict', partSize=0, diskCache=500, repeatMode='?'):
            try:
                ttpassgen.cli.main(['-m', 0, '-d', dictlist, '-r', rule, '-g', repeatMode, '-c', diskCache, '-p', partSize, 'testout.dict'])
            except(SystemExit):
                pass
            return lc()
        global go
        go = go_func


    @classmethod
    def tearDownClass(cls):
        super(Test_ttpassgen, cls).tearDownClass()
        lc = None
        go = None
        os.remove('testout.dict') if os.path.exists('testout.dict') else None
        os.remove('testout.dict.1') if os.path.exists('testout.dict.1') else None
        os.remove('testout.dict.2') if os.path.exists('testout.dict.2') else None
        os.remove('testout.dict.3') if os.path.exists('testout.dict.3') else None
        

    def test_dict_copy_rule(self):
        self.assertEquals(go('$0'), 6)


    def test_charset_rule_no_range(self):
        self.assertEquals(go('[abc]'), 3)


    def test_charset_rule(self):
        self.assertEquals(go('[abc]?'), 4)


    def test_charset_rule_with_range(self):
        self.assertEquals(go('[abc]{2:3}'), 12)


    def test_mask_charset_rule(self):
        self.assertEquals(go('[?d]?'), 4)


    def test_mask_charset_rule(self):
        self.assertEquals(go('[a?dA]{1:2}'), 144)

    def test_mask_charset_rule_with_range(self):
        self.assertEquals(go('[?d]{2:2}'), 90)
        self.assertEquals(go('[?d]{2}'), 90)
    

    def test_dict_mark_charset_rule(self):
        self.assertEquals(go('$0[abc]?'), 24)


    def test_multi_dict_mark_charset_rule(self):
        with open('in2.dict', 'wb') as f:
            content = ['q00', 'q01']
            f.write(('\n'.join(content)).encode('utf-8'))
        self.assertEquals(go('$1$0[abc]?', dictlist='tests/in.dict,in2.dict'), 48)
        os.remove('in2.dict') if os.path.exists('in2.dict') else None


    def test_complex_rule(self):
        self.assertEquals(go('[789]{0:3:*}$0[?q]$0'), 1440)
        self.assertEquals(go('[789]{0:3:*}$0[?q]{1:?}$0'), 1440)

    
    def test_dick_cache(self):
        self.assertEquals(go('$0[abc]?', diskCache=0), 24)

    
    def test_part_size(self):
        os.remove('testout.dict.1') if os.path.exists('testout.dict.1') else None
        os.remove('testout.dict.2') if os.path.exists('testout.dict.2') else None
        os.remove('testout.dict.3') if os.path.exists('testout.dict.3') else None

        go('[?l]{1:4}', partSize=1)
        totalLine = 0
        with open('testout.dict.1', 'r') as f:
            totalLine += len(f.readlines())
        with open('testout.dict.2', 'r') as f:
            totalLine += len(f.readlines())
        if len(ttpassgen._linesep) > 1:
            with open('testout.dict.3', 'r') as f:
                totalLine += len(f.readlines())

        #actual value: 1024 * 1, why 24 difference? I like do it>_>
        self.assertTrue(1000 <= os.path.getsize('testout.dict.1') / 1024 <= 1048)
        os.remove('testout.dict.1') if os.path.exists('testout.dict.1') else None
        os.remove('testout.dict.2') if os.path.exists('testout.dict.2') else None
        os.remove('testout.dict.3') if os.path.exists('testout.dict.3') else None
        self.assertEquals(totalLine, 375076)

    
    def test_wrong_length_in_rule(self):
        os.remove('testout.dict') if os.path.exists('testout.dict') else None
        self.assertEquals(go('[789]{0:-3}'), 0)

    def test_unsupport_rule(self):
        os.remove('testout.dict') if os.path.exists('testout.dict') else None
        self.assertEquals(go('$0word233'), 0)


if __name__ == '__main__':
    unittest.main()
