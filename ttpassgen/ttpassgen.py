#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function
import sys
import click
import re
import itertools
import time
import os
import math
import functools
from multiprocessing import Array
from multiprocessing import Process
from multiprocessing import freeze_support
import threading
from tqdm import tqdm
from collections import OrderedDict
import uuid


_MODES = OrderedDict([(0, 'combination rule mode')])

_BUILT_IN_CHAR_ARRAY = OrderedDict(
    [("?l", "abcdefghijklmnopqrstuvwxyz"),
     ("?u", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"), ("?d", "0123456789"),
     ("?s", "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"), ("?a", "?l?u?d?s"),
     ("?q", "]")])

_REPEAT_MODES = OrderedDict([("?", "0 or 1 repetitions"),
                             ("*", "0 or more repetitions")])

_PART_DICT_NAME_FORMAT = '%s.%d'


# Rule class start

# like char array, wrap with [], format:
# []{minLength:maxLength:repeat_mode}
# []{minLength:maxLength}
# []{length}
class CharArrayRule(object):
    def __init__(self, raw_rule, min_length, max_length, char_array, repeat_mode):
        self.raw_rule = raw_rule
        self.min_length = min_length
        self.max_length = max_length
        self.char_array = char_array
        self.repeat_mode = repeat_mode


# read string from dict_path, format: $dict_index
class DictRule(object):
    def __init__(self, raw_rule, dict_index, dict_path):
        self.raw_rule = raw_rule
        self.dict_index = dict_index
        self.dict_path = dict_path


# normal string, format:
# $(string1){min_repeat:max_repeat:repeat_mode}
# $(string1,string2){min_repeat:max_repeat:repeat_mode}
class StringArrayRule(object):
    def __init__(self, raw_rule, min_repeat, max_repeat, string_array, repeat_mode):
        self.raw_rule = raw_rule
        self.min_repeat = min_repeat
        self.max_repeat = max_repeat
        self.string_array = string_array
        self.repeat_mode = repeat_mode
# Rule class end


class WordProductor(object):
    def __init__(self, count_list, size_list, productors):
        self.count_list = count_list
        self.size_list = size_list
        self.productors = productors

    @classmethod
    def prod(cls, iterable):
        p = 1
        for n in iterable:
            p *= n
        return p

    def total_count(self):
        return self.prod(self.count_list)

    def total_size(self, sep=os.linesep):
        total = 0
        count = self.total_count()
        for i, size in enumerate(self.size_list):
            if self.count_list[i] > 0:
                total += size * count / self.count_list[i]
        total += count * len(sep)
        return total


# Get file display size.
def pretty_size(size_bytes):
    if size_bytes == 0:
        return "0 Bytes"
    # Different operating systems have differences when display file size.
    # on Windows, 1Kb=1024B, actual means 1KiB=1024B.
    # on Mac/Linux, 1KB=1024B.
    # see more: https://en.wikipedia.org/wiki/Gigabyte#Consumer_confusion
    base = 1000
    base = 1024 if os.name == 'nt' else 1000
    size_name = ("Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, base)))
    p = math.pow(base, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def format_dict(d):
    return '\n'.join(['%s = %s' % (key, value) for (key, value) in d.items()])


def get_expanded_char_array(char_array):
    expanded_char_array = char_array
    for (key, value) in _BUILT_IN_CHAR_ARRAY.items():
        expanded_char_array = expanded_char_array.replace(key, value)
    return expanded_char_array


def echo(msg):
    click.echo(msg)


def echo_tips(var_name):
    click.echo(
        "%s is invalid, try use 'ttpassgen --help' for get more information."
        % (var_name))


def get_char_array_rule_data_size(rule):
    size = count = float(0)
    if rule.repeat_mode == '?':
        # not allow element repeat in one word, permutation problem: (n!)/(n-k)!
        for word_length in range(rule.min_length, rule.max_length + 1):
            sub_sum = 1
            for i in range(
                    len(rule.char_array) - word_length + 1,
                    len(rule.char_array) + 1):
                sub_sum *= i
            count += sub_sum
            size += sub_sum * word_length
    else:
        # allow element repeat in one word
        for word_length in range(rule.min_length, rule.max_length + 1):
            count += math.pow(len(rule.char_array), word_length)
            size += count * word_length
    return count, size


def get_string_array_rule_data_size(rule):
    size = count = float(0)
    # normal string
    if rule.min_repeat == 1 and rule.max_repeat == 1 and len(rule.string_array) == 1:
        count += 1
        size += len(rule.raw_rule)
        return count, size

    # string list, only calculate word count.
    size = float(-1)
    if rule.repeat_mode == '?':
        # not allow element repeat in one word, permutation problem: (n!)/(n-k)!
        for repeat_count in range(rule.min_repeat, rule.max_repeat + 1):
            sub_sum = 1
            for i in range(
                    len(rule.string_array) - repeat_count + 1,
                    len(rule.string_array) + 1):
                sub_sum *= i
            count += sub_sum
    else:
        # allow element repeat in one word
        for repeat_count in range(rule.min_repeat, rule.max_repeat + 1):
            count += math.pow(len(rule.string_array), repeat_count)
    return count, size


def get_dict_rule_data_size(rule, inencoding):
    sum_lines = 0
    sepLen = 1
    with open(rule.dict_path, 'r', encoding=inencoding) as f:
        buffer_size = 1024 * 4
        read_func = f.read  # loop optimization
        chunk = read_func(buffer_size)
        sepLen = 2 if '\r\n' in chunk else sepLen
        while chunk:
            sum_lines += chunk.count('\n')
            chunk = read_func(buffer_size)

    # read file last byte for check whether file content end with line separator or not.
    with open(rule.dict_path, 'rb', encoding=inencoding) as f:
        f.seek(-1, os.SEEK_END)
        last_byte = f.read()
        if not last_byte == b'\n':
            sum_lines += 1

    line_separator_count = sepLen * sum_lines
    return sum_lines, (os.path.getsize(rule.dict_path) - line_separator_count)


def char_array_word_productor_wrapper(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        f = func(*args, **kw)
        for item in f:
            yield ''.join(item)  # loop optimization

    return wrapper


@char_array_word_productor_wrapper
def char_array_word_productor(repeat_mode, expanded_char_array, length):
    if repeat_mode == '?':
        return itertools.permutations(expanded_char_array, r=length)
    else:
        return itertools.product(expanded_char_array, repeat=length)


@char_array_word_productor_wrapper
def string_array_word_productor(repeat_mode, string_array, repeat_count):
    if repeat_mode == '?':
        return itertools.permutations(string_array, r=repeat_count)
    else:
        return itertools.product(string_array, repeat=repeat_count)


def large_dict_word_productor(rule, inencoding):
    with open(rule.dict_path, 'r', encoding=inencoding) as f:
        for line in f:
            yield line.strip()


def normal_dict_word_productor(rule, inencoding):
    with open(rule.dict_path, 'r') as f:
        return f.read().splitlines()


def generate_dict_by_rule(mode, dictlist, rule, dict_cache, global_repeat_mode,
                          part_size, append_mode, separator, debug_mode, inencoding,
                          outencoding, output):
    if not dictlist and not rule:
        echo("dictlist and rule option must have at least one value!")
        return
    rules = extract_rules(dictlist, rule, global_repeat_mode)
    if not rules:
        return

    # check if the dictionary file exists.
    dict_files = []
    if dictlist:
        dict_files = re.split(r',\s*', dictlist) if dictlist else []
        for f in dict_files:
            if not os.path.exists(f):
                echo("dict file '%s' does not exist." % (f))
                echo_tips("dictlist")
                return

    if not global_repeat_mode or not re.match(r"\?|\*", global_repeat_mode):
        echo_tips("global_repeat_mode")
        return

    analyzed_rule = [rule1.raw_rule for rule1 in rules]
    print((
        "mode: %s, global_repeat_mode: %s, part_size: %s, dictlist: %s, input dict file encoding: %s"
    ) % (_MODES[mode], global_repeat_mode, pretty_size(part_size * 1024 * 1024), dict_files, inencoding))
    print("raw rule string: %s, analyzed rules: %s" % (rule, analyzed_rule))
    result = Array(
        'i', [0, 0, 0, 0],
        lock=False)  # [count_done, word_count, progress, finish_flag]
    if not debug_mode:
        worker = Process(
            target=product_rule_words,
            args=(result, rules, dict_cache, part_size, append_mode, separator,
                  inencoding, outencoding, output))
    else:
        worker = threading.Thread(
            target=product_rule_words,
            args=(result, rules, dict_cache, part_size, append_mode, separator,
                  inencoding, outencoding, output))
    worker.start()
    # wait product_rule_words() ready
    while not result[0]:
        time.sleep(0.05)
    use_ascii = os.name == 'nt'
    pbar = tqdm(total=result[1], unit=' word', ascii=use_ascii)
    progress = 0
    while progress < pbar.total:
        time.sleep(0.1)
        if result[3]:
            break  # exit
        delta = result[2] - progress
        progress += delta
        pbar.update(delta)
    worker.join()
    if (progress < pbar.total):
        pbar.update(pbar.total - progress)  # avoid stay at 99%
    pbar.close()
    echo("generate dict complete.")


def extract_rules(dictList, rule, global_repeat_mode):
    splited_dict = re.split(r',\s*', dictList) if dictList else []
    dict_count = len(splited_dict)
    re_char_array = r"(\[([^\]]+?)\](\?|(\{-?\d+:-?\d+(:[\?\*])?\})|(\{-?\d+(:[\?\*])?\}))?)"
    re_dict = r"(\$(\d{1,%s}))" % (dict_count if dict_count > 0 else 1)
    re_string_array = r"(\$\((\S+?)\)(\{\d+:\d+(:[\?\*])?\}))"
    re_rule = r"%s|%s|%s" % (re_char_array, re_dict, re_string_array)
    rules = []
    matches_length = 0
    matches = re.findall(re_rule, rule)
    try:
        for match_index, match in enumerate(matches):
            match = list(filter(len, match))  # filter empty element
            matches[match_index] = match
            matches_length += len(match[0])
            if re.match(re_dict, match[0]):
                dict_index = int(match[1])
                dict_rule = DictRule(match[0], dict_index, splited_dict[dict_index])
                rules.append(dict_rule)
            elif re.match(re_string_array, match[0]):
                string_array = match[1].split(',')
                len_info = match[2][1:-1].split(':')
                min_repeat = int(len_info[0])
                max_repeat = int(len_info[1])
                repeat_mode = len_info[2]

                if min_repeat < 0 or max_repeat < 0 or min_repeat > max_repeat \
                        or (min_repeat == 0 and max_repeat == 0):
                    echo("invalid min_repeat: %d or max_repeat: %d, rule: %s" % (min_repeat, max_repeat, match[0]))
                    return None
                if max_repeat > len(string_array):
                    echo("rule '%s' is invalid, max_repeat(%d) cannot be greater than the size of string list(%d)!"
                         % (match[0], max_repeat, len(string_array)))
                    return None
                string_array_rule = StringArrayRule(match[0], min_repeat, max_repeat, string_array, repeat_mode)
                rules.append(string_array_rule)
            else:
                min_length = 0
                max_length = 1
                expanded_char_array = get_expanded_char_array(match[1])
                repeat_mode = global_repeat_mode
                if len(match) > 2:
                    len_info = match[2][1:-1].split(':')
                    if len(len_info) >= 2:
                        if re.match('-?\\d+', len_info[
                                1]):  # check []{min_length:max_length:repeat_mode}
                            min_length = int(len_info[0])
                            max_length = int(len_info[1])
                            if (len(len_info) > 2):
                                repeat_mode = len_info[2]
                        else:
                            min_length = max_length = int(len_info[0])
                            repeat_mode = len_info[1]
                    elif match[2][0] == '{':
                        min_length = max_length = int(len_info[0])  # []{n}
                    else:
                        repeat_mode = len_info[0]  # '?'、'*'
                else:
                    min_length = max_length = 1
                if min_length < 0 or max_length < 0 or min_length > max_length \
                        or (min_length == 0 and max_length == 0):
                    echo("invalid min_repeat: %d or max_repeat: %d, rule: %s" % (min_length, max_length, match[0]))
                    return None
                elif max_length > len(expanded_char_array):
                    echo("rule '%s' is invalid, max_repeat(%d) cannot be greater than the size of char_array(%d)!"
                         % (match[0], max_length, len(expanded_char_array)))
                    return None
                char_array_rule = CharArrayRule(match[0], min_length, max_length,
                                                expanded_char_array, repeat_mode)
                rules.append(char_array_rule)

        # scan whole rule string, unrecognized charactor fragments are treated as normal strings,
        # appear 1 time, so repeat_mode is useless.
        normal_string_rules = []
        # use uuid as divider, then split out normal string.
        divider = '__' + str(uuid.uuid4()) + '__'
        copyed_rule = rule
        for match in matches:
            copyed_rule = copyed_rule.replace(match[0], divider, 1)
        normal_string_rules = copyed_rule.split(divider)

        # insert normal string rule, remain rule's order
        insert_index = 0
        for string_rule in normal_string_rules:
            if not string_rule:
                # empty string, skip insert
                insert_index += 1
            else:
                echo("found normal string: %s" % (string_rule))
                string_array_rule = StringArrayRule(string_rule, 1, 1, [string_rule], global_repeat_mode)
                rules.insert(insert_index, string_array_rule)
                insert_index += 2
    except IndexError:
        echo_tips('rule')
        return None
    if not rules:
        echo_tips("rule")
    return rules


def generate_words_productor(rules, dict_cache_limit, inencoding):
    word_count_list = []
    word_size_list = []
    word_productors = []
    dict_caches = {}
    result_cache = dict_cache_limit
    for rule in rules:
        if isinstance(rule, CharArrayRule):
            word_count, word_size = get_char_array_rule_data_size(rule)
            word_count_list.append(word_count)
            word_size_list.append(word_size)
            p = []
            for repeat_count in range(rule.min_length, rule.max_length + 1):
                p.append(
                    char_array_word_productor(rule.repeat_mode, rule.char_array,
                                              repeat_count))
            word_productors.append(itertools.chain(*p) if len(p) > 1 else p[0])
        elif isinstance(rule, StringArrayRule):
            word_count, word_size = get_string_array_rule_data_size(rule)
            word_count_list.append(word_count)
            if word_size < 0:
                echo("skip calculate StringArrayRule size, rule: %s" % (rule.raw_rule))
                word_size_list.append(0)
            else:
                word_size_list.append(word_size)
            p = []
            for repeat_count in range(rule.min_repeat, rule.max_repeat + 1):
                p.append(
                    string_array_word_productor(rule.repeat_mode, rule.string_array,
                                                repeat_count))
            word_productors.append(itertools.chain(*p) if len(p) > 1 else p[0])
        else:
            if rule.dict_path in dict_caches:
                word_productors.append(dict_caches[rule.dict_path])
            else:
                file_size = os.path.getsize(rule.dict_path)
                if file_size > result_cache:
                    word_productors.append(large_dict_word_productor(rule, inencoding))
                else:
                    dict_caches[rule.dict_path] = normal_dict_word_productor(
                        rule, inencoding)
                    word_productors.append(dict_caches[rule.dict_path])
                    result_cache -= file_size
            word_count, word_size = get_dict_rule_data_size(rule, inencoding)
            word_count_list.append(word_count)
            word_size_list.append(word_size)
    return WordProductor(word_count_list, word_size_list, word_productors)


def product_rule_words(result, rules, dict_cache_limit, part_size, append_mode,
                       separator, inencoding, outencoding, output):
    productor = generate_words_productor(rules, dict_cache_limit, inencoding)
    result[1] = int(productor.total_count())
    result[0] = 1

    word_separator = os.linesep
    if separator:
        word_separator = separator

    estimated_size = pretty_size(productor.total_size(sep=word_separator))
    print(("estimated display size: %s, generate dict...") % (estimated_size))

    if not os.path.exists(
            os.path.abspath(os.path.join(output, os.path.pardir))):
        os.makedirs(os.path.abspath(os.path.join(output, os.path.pardir)))
    real_part_size = part_size * 1024 * 1024
    part_index = 1
    curr_size = 0
    first_output_file_name = output
    if real_part_size:
        first_output_file_name = _PART_DICT_NAME_FORMAT % (output, part_index)

    file_mode = 'ab' if append_mode else 'wb'
    progress = 0

    def progress_monitor():
        while not result[3]:
            result[2] = progress
            time.sleep(0.1)

    threading.Thread(target=progress_monitor).start()

    try:
        p = itertools.product(*productor.productors) if len(
            productor.productors) > 1 else productor.productors[0]
        f = open(first_output_file_name, file_mode)

        if sys.version_info < (3, 0):
            echo('python 2.x not supported')
            return
        if real_part_size:  # avoid condition code cost time.
            # complex rule, more join cost.
            if len(productor.productors) > 1:
                for w in p:
                    content = (''.join(w) + word_separator).encode(outencoding)
                    f.write(content)
                    progress += 1
                    line_length = len(content)
                    curr_size += line_length
                    if curr_size > real_part_size:
                        curr_size = line_length
                        f.close()
                        part_index += 1
                        f = open(
                            _PART_DICT_NAME_FORMAT % (output, part_index),
                            file_mode)
            else:
                for w in p:
                    content = (w + word_separator).encode(outencoding)
                    f.write(content)
                    progress += 1
                    line_length = len(content)
                    curr_size += line_length
                    if curr_size > real_part_size:
                        curr_size = line_length
                        f.close()
                        part_index += 1
                        f = open(
                            _PART_DICT_NAME_FORMAT % (output, part_index),
                            file_mode)
        else:
            # complex rule, more join cost.
            if len(productor.productors) > 1:
                for w in p:
                    f.write((''.join(w) + word_separator).encode(outencoding))
                    progress += 1
            else:
                for w in p:
                    f.write((w + word_separator).encode(outencoding))
                    progress += 1
    finally:
        f.close()
        result[3] = 1


@click.command()
@click.option(
    "--mode",
    "-m",
    show_default=True,
    default=0,
    type=click.INT,
    help="generation mode:\n\n" + format_dict(_MODES))
@click.option(
    "--dictlist",
    "-d",
    type=click.STRING,
    help="read wordlist from the file, multi files should by seperated by comma."
)
@click.option(
    "--rule",
    "-r",
    type=click.STRING,
    show_default=True,
    default="",
    help=
    "define word format, $0 means refer first file in dictlist option, some built-in char_arrays:\n\n"
    + format_dict(_BUILT_IN_CHAR_ARRAY)
    + "\n\nexample: [?dA]{1:2}$0\nview github *Examples* section for more information.")
@click.option(
    "--dict_cache",
    "-c",
    type=click.INT,
    show_default=True,
    default=500,
    help=
    "each element in 'dictlist' option represents a dict file path, this option define"

    + " the maximum amount of memory(MB) that can be used when reading their contents,"

    + "increasing this value when the file is large may increase the build speed."
)
@click.option(
    "--global_repeat_mode",
    "-g",
    show_default=True,
    default='?',
    type=click.STRING,
    help="global repeat mode, the value is used when the repeat mode of rule is not specified:\n\n"
    + format_dict(_REPEAT_MODES))
@click.option(
    "--part_size",
    "-p",
    type=click.INT,
    default=0,
    show_default=True,
    help=
    "when result data is huge, split package size(MB) will be applied, 0 is unlimited."
)
@click.option(
    "--append_mode",
    "-a",
    type=click.INT,
    default=0,
    show_default=True,
    help="whether append content to OUTPUT or not.")
@click.option(
    "--separator",
    "-s",
    type=click.STRING,
    default='',
    show_default=True,
    help=
    "word separator for output file, by default, Mac/Linudx: \n, Windows: \r\n")
@click.option(
    "--debug_mode",
    type=click.INT,
    default=0,
    show_default=True,
    help="set 1 for debug code, only for developer.")
@click.option(
    "--inencoding",
    type=click.STRING,
    default=None,
    show_default=True,
    help="dict file encoding.")
@click.option(
    "--outencoding",
    type=click.STRING,
    default='utf-8',
    show_default=True,
    help="output file encoding.")
@click.argument("output", type=click.Path())
def cli(mode, dictlist, rule, dict_cache, global_repeat_mode, part_size,
        append_mode, separator, debug_mode, inencoding, outencoding, output):
    if mode in _MODES:
        generate_dict_by_rule(mode, dictlist, rule, dict_cache,
                              global_repeat_mode, part_size, append_mode,
                              separator, debug_mode, inencoding, outencoding, output)
    else:
        echo(
            "unknown mode, try use 'ttpassgen --help' for get more information."
        )


if __name__ == "__main__":
    freeze_support()

    # for debug
    # cli.main(['-d', 'tests/in.dict', '-r', '[?d]{7}', '--debug_mode', '1', 'out.txt'])
    cli()
