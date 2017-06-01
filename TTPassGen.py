#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function
from collections import OrderedDict
import sys
import click
import re
import itertools
import time
import os
import math, functools
from multiprocessing import Process, Array
import threading
from tqdm import tqdm

_modes = OrderedDict([
    (0, 'combination rule mode')
])

_built_in_charset = OrderedDict([
    ("?l", "abcdefghijklmnopqrstuvwxyz"),
    ("?u", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
    ("?d", "0123456789"),
    ("?s", "!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"),
    ("?a", "?l?u?d?s"),
    ("?q", "]")
])

_repeat_modes = OrderedDict([
    ("?", "0 or 1 repetitions"),
    ("*", "0 or more repetitions")
])

_part_dict_name_format = '%s.%d'

class CharsetRule(object):
    def __init__(self, minLength, maxLength, charset, repeatMode):
        self.minLength = minLength;
        self.maxLength = maxLength;
        self.charset = charset;
        self.repeatMode = repeatMode;


class DictRule(object):
    def __init__(self, order, dictPath):
        self.order = order;
        self.dictPath = dictPath;


class WordProductor(object):
    def __init__(self, countList, sizeList, productors):
        self.countList = countList
        self.sizeList = sizeList
        self.productors = productors

    def prod(self, iterable):
        p= 1
        for n in iterable: p *= n
        return p

    def totalCount(self):
        return self.prod(self.countList)
    
    def totalSize(self):
        return self.prod(self.sizeList)


def prettySize(size_bytes):
    if size_bytes == 0:
       return "0 Bytes"
    size_name = ("Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

def formatDict(d):
    return '\n'.join(['%s = %s' % (key, value) for (key, value) in d.items()])


def getExpandedCharset(charset):
    expandedCharset = charset
    for (key, value) in _built_in_charset.items():
        expandedCharset = expandedCharset.replace(key, value)
    return expandedCharset


def echoCommonTips(varName):
    click.echo(
        "%s is invalid, , try use 'python TDictGen.py --help' for get more information." % (varName))


def getCharsetRuleResultDataSize(rule):
    size = count = float(0)
    if rule.repeatMode == '?':
        for wordLength in range(rule.minLength, rule.maxLength + 1):
            subSum = 1
            for i in range(len(rule.charset) - wordLength + 1, len(rule.charset) + 1):
                subSum *= i
            count += subSum
            size += subSum * (wordLength + len('\n'))
    else:
        for wordLength in range(rule.minLength, rule.maxLength + 1):
            count += math.pow(len(rule.charset), wordLength)
            size += count * wordLength
    return count, size

def getDictRuleResultDataSize(rule):
    sumLines = 0
    with open(rule.dictPath, 'r') as f:
        bufferSize = 1024 * 4
        readFunc = f.read #loop optimization
        chunk = readFunc(bufferSize)
        while chunk:
            sumLines += chunk.count('\n')
            chunk = readFunc(bufferSize)
    return sumLines, os.path.getsize(rule.dictPath)


def charsetWordProductorWrapper(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        f = func(*args, **kw)
        for item in f:
            yield ''.join(item) #loop optimization
    return wrapper

@charsetWordProductorWrapper    
def charsetWordProductor(repeatMode, expandedCharset, length):
    if repeatMode == '?':
        return itertools.permutations(expandedCharset, r=length)
    else:
        return itertools.product(expandedCharset, repeat=length)

def largeDictWordProductor(rule):
    #NTFS default block size is 4096 bytes or bigger, try align it.
    with open(rule.dictPath, 'r', buffering=1024 * 4) as f:
        for line in f:
            yield line.strip()


def normalDictWordProductor(rule):
    with open(rule.dictPath, 'r') as f:
        return f.read().splitlines()
    

def generateCombinationDict(mode, dictList, rule, dictCache, globalRepeatMode, partSize, output):
    if not dictList and not rule:
        click.echo("dictlist and rule option must have at least one value!")
        return
    rules = extractRules(dictList, rule, globalRepeatMode)
    if not rules:
        echoCommonTips("rule")
        return
    dictFiles = []
    if dictList:
        dictFiles = dictList.split(',')
        for f in dictFiles:
            if not os.path.exists(f):
                echoCommonTips("dictlist")
                return
            
    if not globalRepeatMode or not re.match(r"\??\*?", globalRepeatMode):
        echoCommonTips("global_repeat_mode")

    print(("mode: %s, global_repeat_mode: %s, part_size: %s, dictlist: %s, rule: %s")
               % (_modes[mode], globalRepeatMode, prettySize(partSize * 1024 * 1024), dictFiles, rule))
    result = Array('i', [0, 0, 0, 0], lock=False) #[countDone, wordCount, progress, finishFlag]
    p = Process(target=productCombinationWords, args=(rules, dictCache, partSize, output, result))
    p.start()
    while not result[0]: time.sleep(0.05)
    pbar = tqdm(total=result[1], unit=' word')
    progress = 0
    while progress < pbar.total:
        time.sleep(0.1)
        if result[3]: break #exit
        delta = result[2] - progress
        progress += delta
        pbar.update(delta)
    p.join()
    pbar.update(pbar.total - progress)  #avoid stay at 99%
    pbar.close()
    click.echo("generate dict complete.")


def extractRules(dictList, rule, globalRepeatMode):
    splitedDict = re.split(r'[\s\,]+', dictList) if dictList else []
    reCharset = r"(\[([^\]]+?)\](\?|(\{\d+:\d+(:[\?\*])?\}))?)"
    reDict = r"(\{(\d+)\})"
    reRule = r"%s|%s"%(reCharset, reDict)
    match = re.match(reRule, rule)
    if not match:
        return None

    rules = []
    matches = re.findall(reRule, rule)
    matchesLength = 0
    try:
        for match in matches:
            match = filter(len, match) #may have some empty element
            matchesLength += len(match[0])
            if re.match(reDict, match[0]):
                order = int(match[1])
                dictRule = DictRule(order, splitedDict[order])
                rules.append(dictRule)
            else:
                minLength = 0
                maxLength = 1
                expandedCharset = getExpandedCharset(match[1])
                repeatMode = globalRepeatMode
                if len(match) > 2:
                    lenInfo = match[2][1:-1].split(':')
                    if len(lenInfo) >= 2:
                        minLength = int(lenInfo[0])
                        maxLength = int(lenInfo[1])
                        if (len(lenInfo) > 2):
                            repeatMode = lenInfo[2]
                    else:
                        repeatMode = lenInfo[0]    #?
                else:
                    minLength = maxLength = 1
                if minLength < 0 or maxLength < 0 or minLength > maxLength or len(expandedCharset) < maxLength:
                    return None
                charsetRule = CharsetRule(minLength, maxLength, expandedCharset, repeatMode)
                rules.append(charsetRule)
    except IndexError:
        return None
    if not len(rule) == matchesLength: return None
    return rules


def generateWordProductor(rules, dictCacheLimit):
    wordCountList = []
    wordSizeList = []
    wordProductors = []
    dictCaches = {}
    restCache = dictCacheLimit
    for ruleObj in rules:
        if isinstance(ruleObj, CharsetRule):
            wordCount, wordSize = getCharsetRuleResultDataSize(ruleObj)
            wordCountList.append(wordCount)
            wordSizeList.append(wordSize)
            p = []
            for length in range(ruleObj.minLength, ruleObj.maxLength + 1):
                p.append(charsetWordProductor(ruleObj.repeatMode, ruleObj.charset, length))
            wordProductors.append(itertools.chain(*p) if len(p) > 1 else p[0])
        else:
            if ruleObj.dictPath in dictCaches:
                wordProductors.append(dictCaches[ruleObj.dictPath])
            else:
                fileSize = os.path.getsize(ruleObj.dictPath)
                if fileSize > restCache:
                    wordProductors.append(largeDictWordProductor(ruleObj))
                else:
                    dictCaches[ruleObj.dictPath] = normalDictWordProductor(ruleObj)
                    wordProductors.append(dictCaches[ruleObj.dictPath])
                    restCache -= fileSize
            wordCount, wordSize = getDictRuleResultDataSize(ruleObj)
            wordCountList.append(wordCount)
            wordSizeList.append(wordSize)
    return WordProductor(wordCountList, wordSizeList, wordProductors)       


def productCombinationWords(rules, dictCacheLimit, partSize, output, result):
    productor = generateWordProductor(rules, dictCacheLimit)
    result[1] = int(productor.totalCount())
    result[0] = 1
    estimatedSize = prettySize(productor.totalSize())
    print(("estimated size: %s, generate dict...")%(estimatedSize))

    if not os.path.exists(os.path.abspath(os.path.join(output, os.path.pardir))):
        os.makedirs(os.path.abspath(os.path.join(output, os.path.pardir)))
    realPartSize = partSize * 1024 * 1024
    partIndex = 1
    currSize = 0
    firstOutputFileName = output
    if realPartSize: firstOutputFileName = _part_dict_name_format%(output, partIndex)

    progress = 0
    def progressMonitor():
        while not result[3]:
            result[2] = progress
            time.sleep(0.1)
    threading.Thread(target=progressMonitor).start()

    try:
        p = itertools.product(*productor.productors) if len(productor.productors) > 1 else productor.productors[0]
        f = open(firstOutputFileName, 'wb', buffering=1024 * 4)
        if realPartSize:  # avoid condition code cost.
            if len(productor.productors) > 1:  # complex rule
                for w in p:
                    f.write(''.join(w) + '\n')
                    progress += 1
                    lineLength = len(w) + 1
                    currSize += lineLength
                    if currSize > realPartSize:
                        currSize = lineLength
                        f.close()
                        partIndex += 1
                        f = open(_part_dict_name_format % (
                            output, partIndex), 'wb', buffering=1024 * 4)
            else:
                for w in p:
                    f.write(w + '\n')
                    progress += 1
                    lineLength = len(w) + 1
                    currSize += lineLength
                    if currSize > realPartSize:
                        currSize = lineLength
                        f.close()
                        partIndex += 1
                        f = open(_part_dict_name_format % (
                            output, partIndex), 'wb', buffering=1024 * 4)
        else:
            if len(productor.productors) > 1:  #complex rule
                for w in p:
                    f.write(''.join(w) + '\n')
                    progress += 1
            else:
                for w in p:
                    f.write(w + '\n')
                    progress += 1
    finally:
        f.close()
    result[3] = 1

@click.command()
@click.option("--mode", "-m", show_default=True, default=0, type=click.INT, help="generation mode:\n\n" + formatDict(_modes))
@click.option("--dictlist", "-d", type=click.STRING, help="read wordlist from the file")
@click.option("--rule", "-r", type=click.STRING, show_default=True, default="", 
              help="define word format, {0} means refer first file in wordlist, some built-in charsets:\n\n"
                + formatDict(_built_in_charset) + "\n\nexample: [?dA]{1:2}{0}\nview documentation for more information.")
@click.option("--dict_cache", "-c", type=click.INT, show_default=True, default=500,
              help="each element in 'dictlist' option represents a dict file path, this option define"
                + " the maximum amount of memory(MB) that can be used when reading their contents."
                + "increasing the cache may speed up the build when input dict files is huge.")
@click.option("--global_repeat_mode", "-g", show_default=True, default='?', type=click.STRING,
              help="whether the character is allowd to repeat:\n\n" + formatDict(_repeat_modes))
@click.option("--part_size", "-p", type=click.INT, default=0, show_default=True,
              help="when result data is huge, split package size(MB) will be applied, 0 is unlimited.")
@click.argument("output", type=click.Path())
def cli(mode, dictlist, rule, dict_cache, global_repeat_mode, part_size, output):
    if mode in _modes:
        generateCombinationDict(mode, dictlist, rule, dict_cache, global_repeat_mode, part_size, output)
    else:
        click.echo(
            "unknown mode, try use 'python TDictGen.py --help' for get more information.")


if __name__ == "__main__":
    cli()
