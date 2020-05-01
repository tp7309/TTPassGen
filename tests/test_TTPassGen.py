# coding: utf-8

from __future__ import print_function
from ttpassgen import ttpassgen
import unittest
import os
import shutil

tests_path = os.path.dirname(os.path.abspath(__file__))

lc = None
go = None


# tests/in.dict generate by: ttpassgen -r "[123]{3}" in.dict
class Test_ttpassgen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(Test_ttpassgen, cls).setUpClass()

        def lc_func():
            if not os.path.exists('testout.dict'):
                return 0
            with open('testout.dict', 'r') as f:
                return len(f.readlines())

        global lc
        lc = lc_func

        def go_func(rule,
                    dictlist=os.path.join(tests_path, 'in.dict'),
                    mode=0,
                    partSize=0,
                    diskCache=500,
                    repeatMode='?',
                    separator=None,
                    debugMode=1,
                    output='testout.dict'):
            try:
                ttpassgen.cli.main([
                    '-m', mode, '-d', dictlist, '-r', rule, '-g', repeatMode,
                    '-c', diskCache, '-p', partSize, '-s', separator,
                    '--debug_mode', debugMode, output
                ])
            except (SystemExit):
                pass
            return lc()

        global go
        go = go_func

    @classmethod
    def tearDownClass(cls):
        super(Test_ttpassgen, cls).tearDownClass()
        if os.path.exists(os.path.join(tests_path, 'in3.dict')):
            os.remove(os.path.join(tests_path, 'in3.dict'))
        if os.path.exists('testout.dict'):
            os.remove('testout.dict')
        if os.path.exists('testout.dict.1'):
            os.remove('testout.dict.1')
        if os.path.exists('testout.dict.2'):
            os.remove('testout.dict.2')
        if os.path.exists('testout.dict.3'):
            os.remove('testout.dict.3')

    def test_invalid_options(self):
        if os.path.exists('testout.dict'):
            os.remove('testout.dict')
        self.assertEquals(go('$0', mode=233), 0)

        if os.path.exists('testout.dict'):
            os.remove('testout.dict')
        self.assertEquals(go(dictlist=None, rule=None), 0)

        if os.path.exists('testout.dict'):
            os.remove('testout.dict')
        self.assertEquals(go('[?d]', repeatMode="cc9"), 0)

        if os.path.exists('testout.dict'):
            os.remove('testout.dict')
        self.assertEquals(go('$0word233', dictlist=''), 0)

        if os.path.exists('testout.dict'):
            os.remove('testout.dict')
        self.assertEquals(go('$99[hello]'), 0)

        if os.path.exists('testout.dict'):
            os.remove('testout.dict')
        self.assertEquals(go('$0', dictlist='not_exist.dict'), 0)

        if os.path.exists('testout.dict'):
            os.remove('testout.dict')
        self.assertEquals(go(''), 0)

        if os.path.exists('testout.dict'):
            os.remove('testout.dict')
        self.assertEquals(go('[?d]{0}'), 0)

    def test_not_exist_output_file(self):
        if os.path.exists('testout.dict'):
            os.remove('testout.dict')
        self.assertEquals(go('$0'), 6)

        # check not exist directory.
        if os.path.exists('tempDir'):
            shutil.rmtree('tempDir')
        self.assertEquals(go('$0', output='tempDir/testout.dict'), 6)
        if os.path.exists('tempDir'):
            shutil.rmtree('tempDir')

    def test_dict_copy_rule(self):
        self.assertEquals(go('$0'), 6)

    def test_char_array_rule_no_range(self):
        self.assertEquals(go('[abc]'), 3)

    def test_char_array_rule(self):
        self.assertEquals(go('[abc]?'), 4)

    def test_char_array_rule_with_range(self):
        self.assertEquals(go('[abc]{2:3}'), 12)

    def test_char_array_rule_with_global_repeat_mode(self):
        self.assertEquals(go('[abc]{2:3}', repeatMode='*'), 36)

    def test_mask_char_array_rule(self):
        self.assertEquals(go('[?d]?'), 11)

    def test_mask_char_array_rule_with_range(self):
        self.assertEquals(go('[a?dA]{1:2}'), 144)
        self.assertEquals(go('[?d]{2:2}'), 90)
        self.assertEquals(go('[?d]{2}'), 90)

    def test_dict_mark_char_array_rule(self):
        self.assertEquals(go('$0[abc]?'), 24)

    def test_word_separator(self):
        self.assertEquals(go('$0[abc]?', separator=' '), 1)
        self.assertEquals(
            go('$0[abc]?', separator='-------------------------\n'), 24)

    def test_multi_dict_mark_char_array_rule(self):
        dict_in = os.path.join(tests_path, 'in.dict')
        dict_in2 = os.path.join(tests_path, 'in2.dict')
        with open(dict_in2, 'wb') as f:
            content = ['q00', 'q01']
            f.write(('\n'.join(content)).encode('utf-8'))
        self.assertEquals(
            go('$1$0[abc]?', dictlist="%s,%s" % (dict_in, dict_in2)), 48)
        if os.path.exists(dict_in2):
            os.remove(dict_in2)

    def test_char_array_size(self):
        go('[?d]{2}')
        if os.name == 'nt':
            # default line separator is '\r\n' on windows.
            self.assertTrue(os.path.getsize('testout.dict') == 360)
        else:
            self.assertTrue(os.path.getsize('testout.dict') == 270)

    def test_char_array_estimated_size(self):
        go('[?d]{7}')
        size = os.path.getsize('testout.dict')
        if os.name == 'nt':
            self.assertEquals(ttpassgen.pretty_size(size), "4.61 MB")
        else:
            self.assertEquals(ttpassgen.pretty_size(size), "4.84 MB")

    def test_part_size_with_complex_rule(self):
        if os.path.exists('testout.dict.1'):
            os.remove('testout.dict.1')
        if os.path.exists('testout.dict.2'):
            os.remove('testout.dict.2')
        if os.path.exists('testout.dict.3'):
            os.remove('testout.dict.3')

        go('[?d]{1:4:*}$0[?q]$[123]', partSize=1, debugMode=1)
        total_line = 0
        with open('testout.dict.1', 'r') as f:
            total_line += len(f.readlines())
        with open('testout.dict.2', 'r') as f:
            total_line += len(f.readlines())
        with open('testout.dict.3', 'r') as f:
            total_line += len(f.readlines())

        # actual value: 1024 * 1, why 24 difference? I like do it>_>
        self.assertTrue(
            1000 <= os.path.getsize('testout.dict.1') / 1024 <= 1048)
        if os.path.exists('testout.dict.1'):
            os.remove('testout.dict.1')
        if os.path.exists('testout.dict.2'):
            os.remove('testout.dict.2')
        if os.path.exists('testout.dict.3'):
            os.remove('testout.dict.3')
        self.assertEquals(total_line, 199980)

    def test_multiprocessing_complex_rule(self):
        self.assertEquals(go('[789]{0:3:*}$0[?q]$0', debugMode=0), 1440)
        self.assertEquals(go('[789]{0:3:*}$0[?q]{1:?}$0', debugMode=0), 1440)

    def test_dick_cache(self):
        self.assertEquals(go('$0[abc]?', diskCache=0), 24)

    def test_part_size(self):
        if os.path.exists('testout.dict.1'):
            os.remove('testout.dict.1')
        if os.path.exists('testout.dict.2'):
            os.remove('testout.dict.2')
        if os.path.exists('testout.dict.3'):
            os.remove('testout.dict.3')

        go('[?l]{1:4}', partSize=1)
        total_line = 0
        with open('testout.dict.1', 'r') as f:
            total_line += len(f.readlines())
        with open('testout.dict.2', 'r') as f:
            total_line += len(f.readlines())
        if len(os.linesep) > 1:
            with open('testout.dict.3', 'r') as f:
                total_line += len(f.readlines())

        # actual value: 1024 * 1, why 24 difference? I like do it>_>
        self.assertTrue(
            1000 <= os.path.getsize('testout.dict.1') / 1024 <= 1048)
        if os.path.exists('testout.dict.1'):
            os.remove('testout.dict.1')
        if os.path.exists('testout.dict.2'):
            os.remove('testout.dict.2')
        if os.path.exists('testout.dict.3'):
            os.remove('testout.dict.3')
        self.assertEquals(total_line, 375076)

    def test_wrong_length_in_char_array(self):
        if os.path.exists('testout.dict'):
            os.remove('testout.dict')
        self.assertEquals(go('[789]{0:-3}'), 0)

    def test_max_length_greater_than_char_array_size(self):
        if os.path.exists('testout.dict'):
            os.remove('testout.dict')
        self.assertEquals(go('[789]{2:5}'), 0)

    def test_only_normal_string(self):
        self.assertEquals(go('abc'), 1)

    def test_string_array(self):
        self.assertEquals(go('$(123,xx,789){2:2:?}'), 6)
        self.assertEquals(go('$(123,xx,789){2:2:*}'), 9)

    def normal_string_with_char_array(self):
        self.assertEquals(go('abc[123]{1:2}'), 9)
        self.assertEquals(go('[123]{1:2}abc'), 9)
        self.assertEquals(go('[123]{1:2}abc[45]'), 18)

    def test_char_array_with_string_array(self):
        self.assertEquals(go('aa$(123,456){1:2:?}bb[xy]cc'), 8)

    def test_dict_with_string_array(self):
        self.assertEquals(go('$0[A]?xy'), 12)

    def test_wrong_length_in_string_array(self):
        if os.path.exists('testout.dict'):
            os.remove('testout.dict')
        self.assertEquals(go('$(123,456){3:2:?}'), 0)

    def test_max_length_greater_than_string_array_size(self):
        if os.path.exists('testout.dict'):
            os.remove('testout.dict')
        self.assertEquals(go('$(123,456){3:4:?}'), 0)

    def test_dict_content_not_end_with_line_separator(self):
        shutil.copy(os.path.join(tests_path, 'in.dict'), 'in3.dict')
        dictlist = "%s,in3.dict" % (os.path.join(tests_path, 'in.dict'))
        # in in3.dict, file content not end with '\n'.
        with open('in3.dict', 'a') as f:
            f.write('end')
        self.assertEquals(go('$1eng', dictlist=dictlist), 7)
        if os.path.exists('in3.dict'):
            os.remove('in3.dict')


if __name__ == '__main__':
    unittest.main()
