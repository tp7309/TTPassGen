# TTPassGen
[![Build Status](https://travis-ci.org/tp7309/TTPassGen.svg?branch=master)](https://travis-ci.org/tp7309/TTPassGen)
[![Coverage Status](https://coveralls.io/repos/github/tp7309/TTPassGen/badge.svg?branch=master)](https://coveralls.io/github/tp7309/TTPassGen?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/25f05aa766c34eea9b9692725237e873)](https://www.codacy.com/app/tp7309/TTPassGen?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=tp7309/TTPassGen&amp;utm_campaign=Badge_Grade)

TTPassGen is a highly flexiable and scriptable password dictionary generator base on Python, you can easily use various rules to generate the desired combination of words.

README i18n: [中文说明](https://github.com/tp7309/TTPassGen/blob/master/README_zh_CN.md)

# Features
- generate password use combination、permulation、conditional rules and so on.
- support all characters or words(from wordlist option) that can make up a password, some built-in charset has been provided, such as alphabetical lists and numeric lists.
- you can specify the order and frequency of each element in the word.
- simple rule format, and easy to use, rule could be defined similar regex's style.
- time-consuming estimates, output size estimates, and real-time progress reports.
- unicode word support by using wordlist option.
- Generation of large amounts of passwords at once, no output size limit.
- it can breakup output by file size.

# Install
`TTPassGen` can be easily installed using pip:
```
pip install ttpassgen
```
if you are using the windows operating system, you could just use the [release version](https://github.com/tp7309/TTPassGen/releases).

# Requirements
Python 2 (version 2.7 or later), or Python 3 (version 3.3 or later).

# Quick Start
> Switch to the project's `ttpassgen` directory if you want use ttpassgen by downloaded source code.

Example: Generate word list output to *out.dict*, the word format is prefix three digits, only allow 1、2、3, appear 2 or 3 times, followed by letter a or b.
```
ttpassgen -r [123]{2:3}[ab] out.dict
```
Done.

# Options
```
C:\Users\tp730>ttpassgen --help
Usage: ttpassgen [OPTIONS] OUTPUT
Options:
  -m, --mode INTEGER             generation mode:

                                 0 = combination rule mode
                                 [default: 0]
  -d, --dictlist TEXT            read wordlist from the file, multi files
                                 should by seperated by comma.
  -r, --rule TEXT                define word format, $0 means refer first
                                 file in wordlist, some built-in charsets:

                                 ?l = abcdefghijklmnopqrstuvwxyz
                                 ?u = ABCDEFGHIJKLMNOPQRSTUVWXYZ
                                 ?d = 0123456789
                                 ?s = !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
                                 ?a = ?l?u?d?s
                                 ?q = ]

                                 example: [?dA]{1:2}$0
                                 view *Examples* section for more information.
                                 [default: '']
  -c, --dict_cache INTEGER       each element in 'dictlist' option represents
                                 a dict file path, this option define the
                                 maximum amount of memory(MB) that can be used,
                                 increasing this value when the file is large 
                                 may increase the build speed.  [default: 500]
  -g, --global_repeat_mode TEXT  whether the character is allowd to repeat:

                                 ? = 0 or 1 repetitions
                                 * = 0 or more repetitions
                                 [default: ?]
  -p, --part_size INTEGER        when result data is huge, split package
                                 size(MB) will be applied, 0 is unlimited.
                                 [default: 0]
  -a, --append_mode INTEGER      whether append content to OUTPUT or not.
                                 [default: 0]
  --help                         Show this message and exit.
```
generated password displayed line by line in `OUTPUT`. It is recommended to use notepad ++ to open file(`utf-8`).

# Examples
**[]**  Used to include charset

## Repeat mode
**[]**  1 repetitions.
`[123] -> 1 2 3`

**[]?** 0 or 1 repetitions
`[123] -> '' 1 2 3`

**[]{m:n:r}**
```
when repeatMode is `?`, [123]{1,2} -> 1 2 3 12 13 21 23 31 32
when repeatMode is `*`, [123]{1,2} -> 1 2 3 11 12 13 21 22 23 31 32 33
```

**[]{m:n}**
default use `global_repeat_mode` option.

**[]{n} or []{n:r}**
same as `[]{n:n:r}`.

**$no** ref dict file index from `dictlist` option.
```
ttpassgen --dictlist in.dict,in2.dict --rule $0[_]?$1 out.dict
when dictlist option defined as `in.dict,in2.dict`,
in.dict content:
word11
word12

in2.dict content:
word21
word22


$0[_]?$1 -> word11word21 word11word22 word11_word21 word11_word22 word12word21 word12word22 word12_word21 word12_word22
```

# Update log
[Update log](https://github.com/tp7309/TTPassGen/blob/master/CHANGES.md)
