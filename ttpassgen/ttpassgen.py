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
import threading
from tqdm import tqdm
from collections import OrderedDict


_MODES = OrderedDict([(0, 'combination rule mode')])

_BUILT_IN_CHARSET = OrderedDict(
    [("?l", "abcdefghijklmnopqrstuvwxyz"),
     ("?u", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"), ("?d", "0123456789"),
     ("?s", "!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"), ("?a", "?l?u?d?s"), ("?q",
                                                                       "]")])

_REPEAT_MODES = OrderedDict([("?", "0 or 1 repetitions"),
                             ("*", "0 or more repetitions")])

_SPECIAL_SEPERATORS_NAME = OrderedDict([("&#160;", "one space")])

_SPECIAL_SEPERATORS = OrderedDict([("&#160;", " ")])

_PART_DICT_NAME_FORMAT = '%s.%d'


# Rule class start
class CharsetRule(object):
    def __init__(self, min_length, max_length, charset, repeat_mode):
        self.min_length = min_length
        self.max_length = max_length
        self.charset = charset
        self.repeat_mode = repeat_mode


class DictRule(object):
    def __init__(self, order, dict_path):
        self.order = order
        self.dict_path = dict_path


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
            total += size * count / self.count_list[i]
        total += count * len(sep)
        return total


def pretty_size(size_bytes):
    if size_bytes == 0:
        return "0 Bytes"
    size_name = ("Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def format_dict(d):
    return '\n'.join(['%s = %s' % (key, value) for (key, value) in d.items()])


def get_expanded_charset(charset):
    expanded_charset = charset
    for (key, value) in _BUILT_IN_CHARSET.items():
        expanded_charset = expanded_charset.replace(key, value)
    return expanded_charset


def echo_tips(var_name):
    click.echo(
        "%s is invalid, , try use 'python TDictGen.py --help' for get more information."
        % (var_name))


def get_charset_rule_data_size(rule):
    size = count = float(0)
    if rule.repeat_mode == '?':
        for word_length in range(rule.min_length, rule.max_length + 1):
            sub_sum = 1
            for i in range(
                    len(rule.charset) - word_length + 1,
                    len(rule.charset) + 1):
                sub_sum *= i
            count += sub_sum
            size += sub_sum * word_length
    else:
        for word_length in range(rule.min_length, rule.max_length + 1):
            count += math.pow(len(rule.charset), word_length)
            size += count * word_length
    return count, size


def get_dict_rule_data_size(rule, inencoding):
    sum_lines = 0
    sepLen = 1
    with open(rule.dict_path, 'r', encoding=inencoding) as f:
        buffer_size = 1024 * 4
        read_func = f.read  # loop optimization
        chunk = read_func(buffer_size)
        if '\r\n' in chunk:
            sepLen = 2
        while chunk:
            sum_lines += chunk.count('\n')
            chunk = read_func(buffer_size)
    line_seperator_count = sepLen * sum_lines
    return sum_lines, (os.path.getsize(rule.dict_path) - line_seperator_count)


def charset_word_productor_wrapper(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        f = func(*args, **kw)
        for item in f:
            yield ''.join(item)  # loop optimization

    return wrapper


@charset_word_productor_wrapper
def charset_word_productor(repeat_mode, expanded_charset, length):
    if repeat_mode == '?':
        return itertools.permutations(expanded_charset, r=length)
    else:
        return itertools.product(expanded_charset, repeat=length)


def large_dict_word_productor(rule, inencoding):
    with open(rule.dict_path, 'r', encoding=inencoding) as f:
        for line in f:
            yield line.strip()


def normal_dict_word_productor(rule, inencoding):
    with open(rule.dict_path, 'r') as f:
        return f.read().splitlines()


def generate_dict_by_rule(mode, dictlist, rule, dict_cache, global_repeat_mode,
                          part_size, append_mode, seperator, debug_mode, inencoding,
                          outencoding, output):
    if not dictlist and not rule:
        click.echo("dictlist and rule option must have at least one value!")
        return
    rules = extract_rules(dictlist, rule, global_repeat_mode)
    if not rules:
        echo_tips("rule")
        return

    dict_files = []
    if dictlist:
        dict_files = re.split(r',\s*', dictlist) if dictlist else []
        for f in dict_files:
            if not os.path.exists(f):
                echo_tips("dictlist")
                return

    if not global_repeat_mode or not re.match(r"\?|\*", global_repeat_mode):
        echo_tips("global_repeat_mode")
        return

    print((
        "mode: %s, global_repeat_mode: %s, part_size: %s, dictlist: %s, dict file encoding: %s, rule: %s"
    ) % (_MODES[mode], global_repeat_mode,
         pretty_size(part_size * 1024 * 1024), dict_files, inencoding, rule))
    result = Array(
        'i', [0, 0, 0, 0],
        lock=False)  # [count_done, word_count, progress, finish_flag]
    if not debug_mode:
        worker = Process(
            target=product_rule_words,
            args=(result, rules, dict_cache, part_size, append_mode, seperator,
                  inencoding, outencoding, output))
    else:
        worker = threading.Thread(
            target=product_rule_words,
            args=(result, rules, dict_cache, part_size, append_mode, seperator,
                  inencoding, outencoding, output))
    worker.start()
    while not result[0]:
        time.sleep(0.05)
    pbar = tqdm(total=result[1], unit=' word')
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
    click.echo("generate dict complete.")


def extract_rules(dictList, rule, global_repeat_mode):
    splited_dict = re.split(r',\s*', dictList) if dictList else []
    dict_count = len(splited_dict)
    re_charset = r"(\[([^\]]+?)\](\?|(\{-?\d+:-?\d+(:[\?\*])?\})|(\{-?\d+(:[\?\*])?\}))?)"
    re_dict = r"(\$(\d{1,%s}))" % (dict_count if dict_count > 0 else 1)
    re_rule = r"%s|%s" % (re_charset, re_dict)
    rules = []
    matches_length = 0
    matches = re.findall(re_rule, rule)
    try:
        for match in matches:
            match = list(filter(len, match))  # may have some empty element
            matches_length += len(match[0])
            if re.match(re_dict, match[0]):
                order = int(match[1])
                dict_rule = DictRule(order, splited_dict[order])
                rules.append(dict_rule)
            else:
                min_length = 0
                max_length = 1
                expanded_charset = get_expanded_charset(match[1])
                repeat_mode = global_repeat_mode
                if len(match) > 2:
                    len_info = match[2][1:-1].split(':')
                    if len(len_info) >= 2:
                        if re.match('-?\d+', len_info[
                                1]):  # []{min_length:max_length:repeat_mode}
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
                        repeat_mode = len_info[0]  # ?
                else:
                    min_length = max_length = 1
                if min_length < 0 or max_length < 0 or min_length > max_length or len(
                        expanded_charset) < max_length:
                    return None
                charset_rule = CharsetRule(min_length, max_length,
                                           expanded_charset, repeat_mode)
                rules.append(charset_rule)
    except IndexError:
        return None
    if matches_length <= 0:
        return None
    return rules


def generate_words_productor(rules, dict_cache_limit, inencoding):
    word_count_list = []
    word_size_list = []
    word_productors = []
    dict_caches = {}
    result_cache = dict_cache_limit
    for rule in rules:
        if isinstance(rule, CharsetRule):
            word_count, word_size = get_charset_rule_data_size(rule)
            word_count_list.append(word_count)
            word_size_list.append(word_size)
            p = []
            for length in range(rule.min_length, rule.max_length + 1):
                p.append(
                    charset_word_productor(rule.repeat_mode, rule.charset,
                                           length))
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
                       seperator, inencoding, outencoding, output):
    productor = generate_words_productor(rules, dict_cache_limit, inencoding)
    result[1] = int(productor.total_count())
    result[0] = 1
    estimated_size = pretty_size(productor.total_size(sep=seperator))
    print(("estimated size: %s, generate dict...") % (estimated_size))

    if not os.path.exists(
            os.path.abspath(os.path.join(output, os.path.pardir))):
        os.makedirs(os.path.abspath(os.path.join(output, os.path.pardir)))
    real_part_size = part_size * 1024 * 1024
    part_index = 1
    curr_size = 0
    first_output_file_name = output
    if real_part_size:
        first_output_file_name = _PART_DICT_NAME_FORMAT % (output, part_index)

    word_seperator = os.linesep
    if seperator:
        word_seperator = _SPECIAL_SEPERATORS[
            seperator] if seperator in _SPECIAL_SEPERATORS else seperator

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

        # wrap f.write('content') as func will reduce the generation speed, so remain if...elif...
        if sys.version_info > (
                3,
                0):  # there will be a minimum of 10% performance improvement.
            if real_part_size:  # avoid condition code cost.
                # complex rule, more join cost.
                if len(productor.productors) > 1:
                    for w in p:
                        content = (''.join(w) + word_seperator).encode(outencoding)
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
                        content = (w + word_seperator).encode(outencoding)
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
                        f.write((''.join(w) + word_seperator).encode(outencoding))
                        progress += 1
                else:
                    for w in p:
                        f.write((w + word_seperator).encode(outencoding))
                        progress += 1
        else:
            print('python 2.x not supported')
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
    "define word format, $0 means refer first file in wordlist, some built-in charsets:\n\n"
    + format_dict(_BUILT_IN_CHARSET) +
    "\n\nexample: [?dA]{1:2}$0\nview documentation for more information.")
@click.option(
    "--dict_cache",
    "-c",
    type=click.INT,
    show_default=True,
    default=500,
    help=
    "each element in 'dictlist' option represents a dict file path, this option define"
    +
    " the maximum amount of memory(MB) that can be used when reading their contents,"
    +
    "increasing this value when the file is large may increase the build speed."
)
@click.option(
    "--global_repeat_mode",
    "-g",
    show_default=True,
    default='?',
    type=click.STRING,
    help="whether the character is allowd to repeat:\n\n" +
    format_dict(_REPEAT_MODES))
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
    "--seperator",
    "-s",
    type=click.STRING,
    default='',
    show_default=True,
    help=
    "word seperator, by default, each word occupies one line. special char:\n\n"
    + format_dict(_SPECIAL_SEPERATORS_NAME))
@click.option(
    "--debug_mode",
    type=click.INT,
    default=0,
    show_default=True,
    help="set 1 for enter debug mode.")
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
        append_mode, seperator, debug_mode, inencoding, outencoding, output):
    if mode in _MODES:
        generate_dict_by_rule(mode, dictlist, rule, dict_cache,
                              global_repeat_mode, part_size, append_mode,
                              seperator, debug_mode, inencoding, outencoding, output)
    else:
        click.echo(
            "unknown mode, try use 'python TTDictGen.py --help' for get more information."
        )


if __name__ == "__main__":
    cli()
    # cli.main(['-d', '../tests/in.dict', '-r', '[?l]{5}', 'out.dict'])
