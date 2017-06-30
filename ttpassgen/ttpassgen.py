#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function
import sys
import click
import re
import itertools
import time
import os
import math, functools
from multiprocessing import Array
import multiprocessing
import threading
from tqdm import tqdm
from collections import OrderedDict


# Module multiprocessing start: organized differently in Python 3.4+
try:
    # Python 3.4+
    if sys.platform.startswith('win'):
        import multiprocessing.popen_spawn_win32 as forking
    else:
        import multiprocessing.popen_fork as forking
except ImportError:
    import multiprocessing.forking as forking

if sys.platform.startswith('win'):
    # First define a modified version of Popen.
    class _Popen(forking.Popen):
        def __init__(self, *args, **kw):
            if hasattr(sys, 'frozen'):
                # We have to set original _MEIPASS2 value from sys._MEIPASS
                # to get --onefile mode working.
                os.putenv('_MEIPASS2', sys._MEIPASS)
            try:
                super(_Popen, self).__init__(*args, **kw)
            finally:
                if hasattr(sys, 'frozen'):
                    # On some platforms (e.g. AIX) 'os.unsetenv()' is not
                    # available. In those cases we cannot delete the variable
                    # but only set it to the empty string. The bootloader
                    # can handle this case.
                    if hasattr(os, 'unsetenv'):
                        os.unsetenv('_MEIPASS2')
                    else:
                        os.putenv('_MEIPASS2', '')

    # Second override 'Popen' class with our modified version.
    forking.Popen = _Popen

class Process(multiprocessing.Process):
    pass
#Module multiprocessing end

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

_special_seperators_name = OrderedDict([
    ("&#160;", "one space")
])

_special_seperators = OrderedDict([
    ("&#160;", " ")
])


_part_dict_name_format = '%s.%d'


#Rule class start
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

    @classmethod
    def prod(cls, iterable):
        p= 1
        for n in iterable: p *= n
        return p

    def totalCount(self):
        return self.prod(self.countList)
    
    def totalSize(self):
        total = 0
        tCount = self.totalCount()
        for i, size in enumerate(self.sizeList):
            total += size * tCount / self.countList[i]
        total += tCount * len(os.linesep)
        return total
#Rule class end


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
            size += subSum * wordLength
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
    linSeperatorCount = len(os.linesep) * sumLines
    return sumLines, (os.path.getsize(rule.dictPath) - linSeperatorCount)


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
    

def generateCombinationDict(mode, dictList, rule, dictCache, globalRepeatMode, partSize, appendMode, seperator, output):
    if not dictList and not rule:
        click.echo("dictlist and rule option must have at least one value!")
        return
    rules = extractRules(dictList, rule, globalRepeatMode)
    if not rules:
        echoCommonTips("rule")
        return
    dictFiles = []
    if dictList:
        dictFiles = re.split(r',\s*', dictList) if dictList else []
        for f in dictFiles:
            if not os.path.exists(f):
                echoCommonTips("dictlist")
                return
            
    if not globalRepeatMode or not re.match(r"\??\*?", globalRepeatMode):
        echoCommonTips("global_repeat_mode")

    print(("mode: %s, global_repeat_mode: %s, part_size: %s, dictlist: %s, rule: %s")
               % (_modes[mode], globalRepeatMode, prettySize(partSize * 1024 * 1024), dictFiles, rule))
    result = Array('i', [0, 0, 0, 0], lock=False) #[countDone, wordCount, progress, finishFlag]
    p = Process(target=productCombinationWords, args=(result, rules, dictCache, partSize, appendMode, seperator, output))
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
    if (progress < pbar.total): pbar.update(pbar.total - progress)  #avoid stay at 99%
    pbar.close()
    click.echo("generate dict complete.")


def extractRules(dictList, rule, globalRepeatMode):
    splitedDict = re.split(r',\s*', dictList) if dictList else []
    dictCount = len(splitedDict)
    reCharset = r"(\[([^\]]+?)\](\?|(\{\d+:\d+(:[\?\*])?\})|(\{\d+(:[\?\*])?\}))?)"
    reDict = r"(\$(\d{1,%s}))"%(dictCount if dictCount > 0 else 1)
    reRule = r"%s|%s"%(reCharset, reDict)
    match = re.match(reRule, rule)
    if not match:
        return None

    rules = []
    matches = re.findall(reRule, rule)
    matchesLength = 0
    try:
        for match in matches:
            match = list(filter(len, match)) #may have some empty element
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
                        if re.match('\d', lenInfo[1]):  #[]{minLength:maxLength:repeatMode}
                            minLength = int(lenInfo[0])
                            maxLength = int(lenInfo[1])
                            if (len(lenInfo) > 2):
                                repeatMode = lenInfo[2]
                        else:
                            minLength = maxLength = int(lenInfo[0])
                            repeatMode = lenInfo[1]
                    elif match[2][0] == '{':
                        minLength = maxLength = int(lenInfo[0])  #[]{n}
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


def productCombinationWords(result, rules, dictCacheLimit, partSize, appendMode, seperator, output):
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

    wordSeperator = os.linesep
    if seperator:
        wordSeperator = _special_seperators[seperator] if seperator in _special_seperators else seperator

    lineSeperatorLength = len(wordSeperator)
    fileMode = 'ab' if appendMode else 'wb'

    progress = 0
    def progressMonitor():
        while not result[3]:
            result[2] = progress
            time.sleep(0.1)
    threading.Thread(target=progressMonitor).start()

    try:
        p = itertools.product(*productor.productors) if len(productor.productors) > 1 else productor.productors[0]
        f = open(firstOutputFileName, fileMode, buffering=1024 * 4)

        if sys.version_info > (3, 0): #there will be a minimum of 10% performance improvement.
            if realPartSize:  # avoid condition code cost.
                if len(productor.productors) > 1:  # complex rule
                    for w in p:
                        f.write((''.join(w) + wordSeperator).encode('utf-8'))
                        progress += 1
                        lineLength = len(w) + lineSeperatorLength
                        currSize += lineLength
                        if currSize > realPartSize:
                            currSize = lineLength
                            f.close()
                            partIndex += 1
                            f = open(_part_dict_name_format % (
                                output, partIndex), fileMode, buffering=1024 * 4)
                else:
                    for w in p:
                        f.write((w + wordSeperator).encode('utf-8'))
                        progress += 1
                        lineLength = len(w) + lineSeperatorLength
                        currSize += lineLength
                        if currSize > realPartSize:
                            currSize = lineLength
                            f.close()
                            partIndex += 1
                            f = open(_part_dict_name_format % (
                                output, partIndex), fileMode, buffering=1024 * 4)
            else:
                if len(productor.productors) > 1:  #complex rule
                    for w in p:
                        f.write((''.join(w) + wordSeperator).encode('utf-8'))
                        progress += 1
                else:
                    for w in p:
                        f.write((w + wordSeperator).encode('utf-8'))
                        progress += 1
        else:
            if realPartSize:  # avoid condition code cost.
                if len(productor.productors) > 1:  # complex rule
                    for w in p:
                        f.write(''.join(w) + wordSeperator)
                        progress += 1
                        lineLength = len(w) + lineSeperatorLength
                        currSize += lineLength
                        if currSize > realPartSize:
                            currSize = lineLength
                            f.close()
                            partIndex += 1
                            f = open(_part_dict_name_format % (
                                output, partIndex), fileMode, buffering=1024 * 4)
                else:
                    for w in p:
                        f.write(w + wordSeperator)
                        progress += 1
                        lineLength = len(w) + lineSeperatorLength
                        currSize += lineLength
                        if currSize > realPartSize:
                            currSize = lineLength
                            f.close()
                            partIndex += 1
                            f = open(_part_dict_name_format % (
                                output, partIndex), fileMode, buffering=1024 * 4)
            else:
                if len(productor.productors) > 1:  #complex rule
                    for w in p:
                        f.write(''.join(w) + wordSeperator)
                        progress += 1
                else:
                    for w in p:
                        f.write(w + wordSeperator)
                        progress += 1
    finally:
        f.close()
    result[3] = 1

@click.command()
@click.option("--mode", "-m", show_default=True, default=0, type=click.INT, help="generation mode:\n\n" + formatDict(_modes))
@click.option("--dictlist", "-d", type=click.STRING,
              help="read wordlist from the file, multi files should by seperated by comma.")
@click.option("--rule", "-r", type=click.STRING, show_default=True, default="",
              help="define word format, $0 means refer first file in wordlist, some built-in charsets:\n\n"
                + formatDict(_built_in_charset) + "\n\nexample: [?dA]{1:2}$0\nview documentation for more information.")
@click.option("--dict_cache", "-c", type=click.INT, show_default=True, default=500,
              help="each element in 'dictlist' option represents a dict file path, this option define"
                + " the maximum amount of memory(MB) that can be used when reading their contents,"
                + "increasing this value when the file is large may increase the build speed.")
@click.option("--global_repeat_mode", "-g", show_default=True, default='?', type=click.STRING,
              help="whether the character is allowd to repeat:\n\n" + formatDict(_repeat_modes))
@click.option("--part_size", "-p", type=click.INT, default=0, show_default=True,
              help="when result data is huge, split package size(MB) will be applied, 0 is unlimited.")
@click.option("--append_mode", "-a", type=click.INT, default=0, show_default=True,
              help="whether append content to OUTPUT or not.")
@click.option("--seperator", "-s", type=click.STRING, default='', show_default=True,
              help="word seperator, by default, each word occupies one line. special char:\n\n" + formatDict(_special_seperators_name))
@click.argument("output", type=click.Path())
def cli(mode, dictlist, rule, dict_cache, global_repeat_mode, part_size, append_mode, seperator, output):
    if mode in _modes:
        generateCombinationDict(mode, dictlist, rule, dict_cache, global_repeat_mode, part_size, append_mode, seperator, output)
    else:
        click.echo(
            "unknown mode, try use 'python TDictGen.py --help' for get more information.")


if __name__ == "__main__":
    # On Windows calling this function is necessary.
    multiprocessing.freeze_support()
    cli()
    # cli.main(['-d', '../tests/in.dict', '-r', '[?d]{2}$0', 'out.dict'])
