# TTPassGen

[![Build Status](https://travis-ci.org/tp7309/TTPassGen.svg?branch=master)](https://travis-ci.org/tp7309/TTPassGen)
[![Coverage Status](https://coveralls.io/repos/github/tp7309/TTPassGen/badge.svg?branch=master)](https://coveralls.io/github/tp7309/TTPassGen?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/25f05aa766c34eea9b9692725237e873)](https://www.codacy.com/app/tp7309/TTPassGen?utm_source=github.com&utm_medium=referral&utm_content=tp7309/TTPassGen&utm_campaign=Badge_Grade)
[![Rawsec's CyberSecurity Inventory](https://inventory.rawsec.ml/img/badges/Rawsec-inventoried-FF5050_flat.svg)](https://inventory.rawsec.ml/tools.html#TTPassGen)

TTPassGen is a highly flexiable and scriptable password dictionary generator base on Python, you can easily use various rules to generate the desired combination of words.

README i18n: [中文说明](https://github.com/tp7309/TTPassGen/blob/master/README_zh_CN.md)

# Features

- generate password use combination、permulation、conditional rules and so on.
- support all characters or words(from wordlist option) that can make up a password, some built-in charset has been provided, such as alphabetical list and numeric list.
- you can specify the order and frequency of each element in the word.
- simple rule format, and easy to use, rule could be defined similar regex's style.
- time-consuming estimates, output size estimates, and real-time progress reports.
- unicode word support by using wordlist option.
- generation of large amounts of passwords at once, no output size limit.
- support split output by file size.

# Install

`TTPassGen` can be easily installed using pip:

```
pip install ttpassgen
```

if you are using the windows operating system, you could just use the [release version](https://github.com/tp7309/TTPassGen/releases).

# Requirements

Python 3.5 or later.

# Quick Start

> Switch to the project's `ttpassgen` directory if you want use ttpassgen by downloaded source code.

Example: Generate word list and output to `out.txt`, the word format is prefix three digits, only allow 1、2、3, appear 2 or 3 times, end with `xyz`.

```
ttpassgen -r "[123]{2:3}xyz" out.txt
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
                                 file in dictlist option, some built-in char arrays:

                                 ?l = abcdefghijklmnopqrstuvwxyz
                                 ?u = ABCDEFGHIJKLMNOPQRSTUVWXYZ
                                 ?d = 0123456789
                                 ?s = !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
                                 ?a = ?l?u?d?s
                                 ?q = ]

                                 example: [?dA]{1:2}$0
                                 view *RuleTypes* section for more information.
                                 [default: '']
  -c, --dict_cache INTEGER       each element in 'dictlist' option represents
                                 a dict file path, this option define the
                                 maximum amount of memory(MB) that can be used,
                                 increasing this value when the file is large
                                 may increase the build speed.  [default: 500]
  -g, --global_repeat_mode TEXT  global repeat mode, the value is used when the repeat mode of rule is not specified:

                                 ? = 0 or 1 repetitions
                                 * = 0 or more repetitions
                                 [default: ?]
  -p, --part_size INTEGER        when result data is huge, split package
                                 size(MB) will be applied, 0 is unlimited.
                                 [default: 0]
  -a, --append_mode INTEGER      whether append content to OUTPUT or not.
                                 [default: 0]
  -s, --seperator TEXT           wword seperator for output file, by default, Mac/Linudx: \n, Windows: \r\n".
                                 [default: Mac/Linux: \n, Windows: \r\n]
  --inencoding TEXT              dict file encoding.
  --outencoding TEXT             output file encoding.  [default: utf-8]
  --help                         Show this message and exit.
```

The output file uses `utf-8` encoding by default, it is recommended to use _Notepad++_ to open this file.

# RuleTypes

**TTPassGen** supports three rule type, which can specified with the `--rule` option, you can use these rules at the same time.

## CharArrayRule

Generate a word based on the defined char array and repeat information.
Rule format：

```
[]{min_repeat:max_repeat:repeat_mode}
```

### CharArray

Use **[]** to wrap all chars.

Built-in char arrays:

```
//lowercase letters
?l = abcdefghijklmnopqrstuvwxyz

//Uppercase letters
?u = ABCDEFGHIJKLMNOPQRSTUVWXYZ

//Number list
?d = 0123456789

//Special character list
?s = !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~

//A collection of the above list
?a = ?l?u?d?s

//']', chars are wrapped with '[]', so if what put ']' into '[]', use '?q' instead of ']'.
?q = ]
```

For example, **[?d]** means to select char from number list.

### RepeatFormat

```
{min_repeat:max_repeat:repeat_mode}
```

For `CharArrayRule`, repeat time is the length of the word to be generated.

- `min_repeat`
  minimum repeat times
- `max_repeat`
  maximum repeat times
- `repeat_mode`
  char repeat mode

Define rule similar regex's style:

**[]** 1 repetitions.
`[123] -> 1 2 3`

**[]?** 0 or 1 repetitions.
`[123]? -> '' 1 2 3`

**[]{m:n:r}** repeat `m` to `n` times.
Repeat mode support `?` and `*`.

- repeatMode is '?', each char appears 0 or 1 times in word.

  `[123]{1:2:?} -> 1 2 3 12 13 21 23 31 32`

- repeatMode is '\*', each char appears 0 or more times in word.

  `[123]{1:2:*} -> 1 2 3 11 12 13 21 22 23 31 32 33`

Short rule format:

- **[]{m:n}**

  same as `[]{m:m:global_repeat_mode}`

- **[]{n}**

  same as `[]{n:n:global_repeat_mode}`

- **[]{n:r}**

  same as `[]{n:n:r}`

### Example

Generate 8-digit numeric password:

```
[?d]{8:8:*} or [?d]{8:*} or [1234567890]{8:8:*}
```

Generate an 8-digit numeric password, and each char in the password can appear at most once. Because the default value of `global repeat mode` is '?', so you can skip set repeat_mode:

```
[?d]{8:8:?} or [?d]{8}
```

Generate a password of 7 to 8 digits in length. The word can be composed of upper and lower case letters, numbers, and `_`:

```
[?l?u?d_]{7:8:*}
```

Use characters 1, 2, and 3 to generate a 4-digit password, and each character can appear at most once in each word:

```
[123]{4}  //Error! the length of word cannot be greater than the char array size.
[123]{2}[123]{2}  //Correct.
```

## StringArrayRule

Generate a word based on the defined string array and repeat information.
Rule format：

- `$(string1,string2){min_repeat:max_repeat:repeat_mode}`

  String array, each string is splited by comma, no spaces.

- `string`

  Normal string, same as `$(string){1:1:?}`.

Like `CharArrayRule`, but `StringArrayRule` does not support `Short rule format`.

### Example

Generate an 8-digit numeric password, end with `abc`:

```
[?d]{8:8:*}abc
```

Choose a number from (10,20,30), then append it after 'age':

```
age$(10,20,30){1:1:?}
```

Choose a number from (10,20,30), then append it after 'age', end with 'x' or 'y':

```
age$(10,20,30){1:1:?}[xy]
```

## DictRule

Read string from file(txt file). The dictionary file path can be specified by the `--dictlist` option. For example,`$0` means to refer 0th dictionary file.

Rule format:

```
$index
```

DictRule not support repeat mode.

### Example

content of `in.txt`:

```
ab
cd
```

content of `in2.txt`:

```
12
34
```

When dictlist option defined as `in.dict,in2.dict` and _seperator_ is one space, run following command：

```bash
ttpassgen --dictlist "in.txt,in2.txt" --rule "$0[_]?$1" -s " " out.txt
```

Output:

```
ab12 ab34 ab_12 ab_34 cd12 cd34 cd_12 cd_34
```
