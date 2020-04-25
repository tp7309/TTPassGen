# TTPassGen

[![Build Status](https://travis-ci.org/tp7309/TTPassGen.svg?branch=master)](https://travis-ci.org/tp7309/TTPassGen)
[![Coverage Status](https://coveralls.io/repos/github/tp7309/TTPassGen/badge.svg?branch=master)](https://coveralls.io/github/tp7309/TTPassGen?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/25f05aa766c34eea9b9692725237e873)](https://www.codacy.com/app/tp7309/TTPassGen?utm_source=github.com&utm_medium=referral&utm_content=tp7309/TTPassGen&utm_campaign=Badge_Grade)
[![Rawsec's CyberSecurity Inventory](https://inventory.rawsec.ml/img/badges/Rawsec-inventoried-FF5050_flat.svg)](https://inventory.rawsec.ml/tools.html#TTPassGen)

TTPassGen 是一个支持灵活定制的密码字典生成器，我们可以轻松地定义各种规则来生成所需的单词组合。因为基于 Python，所以可以跨平台使用。

# 特性

- 使用组合，排列，条件规则等生成密码。
- 支持可以组成密码的所有字符或单词（从 wordlist 选项中获取输入字典路径），有内置字符集，例如字母列表和数字列表。
- 可以指定单词中每个元素出现的顺序和频率。
- 规则格式非常容易学习，程序易于使用，规则定义采用类似于正则表达式的风格。
- 提供生成密码词典的耗时预估，输出文件大小预估和实时进度报告。
- 使用 wordlist 选项可以支持中文之类的 unicode 字符组成密码。
- 可以一次生成大量密码，无输出大小限制。
- 支持通过设置每个输出字典的大小来将数据输出到多个文件，防止单个字典过大。

# 安装

`TTPassGen` 可以使用 Python 的`pip`轻松安装:

```
pip install ttpassgen
```

如果你使用的是 Windows 操作系统，可以直接下载[release version](https://github.com/tp7309/TTPassGen/releases)，这样就不需要 Python 环境了。

# 使用要求

Python 3.5 或其之后的版本。
如果你使用的是 Windows 操作系统，不需要 Python 环境，也可以直接下载[release version](https://github.com/tp7309/TTPassGen/releases)。

# 快速使用

> 如果是使用 ttpassgen.exe 文件，那么注意最好在 Windows 的命令提示符窗口下执行命令。

示例：生成单词列表输出到文件 out.txt，单词格式为最前面是三个数字，只允许 1、2、3，重复 2 或 3 次，以`xyz`结尾。

```
ttpassgen -r "[123]{2:3}xyz" out.txt
```

可以打开 out.dict 查看结果（建议用 Notepad++打开）。

# 配置项

```
C:\Users\tp730>ttpassgen --help
Usage: ttpassgen [OPTIONS] OUTPUT
Options:
  -m, --mode INTEGER             指定生成模式:

                                 0 = 规则定义模式
                                 [默认值: 0]
  -d, --dictlist TEXT            定义要在--rule选项引用的字典文件路径，
                                 有多个路径的话用逗号隔开。

  -r, --rule TEXT                定义用于生成的密码的规则, $0 意思指定引用--dictlist选项中的第0个文件, 内建字符集:

                                 ?l = abcdefghijklmnopqrstuvwxyz
                                 ?u = ABCDEFGHIJKLMNOPQRSTUVWXYZ
                                 ?d = 0123456789
                                 ?s = !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
                                 ?a = ?l?u?d?s
                                 ?q = ]

                                 示例: [?dA]{1:2}$0
                                 查看*规则格式*节以了解更多信息.
                                 [默认值: '']
  -c, --dict_cache INTEGER       读取--dictlist选项中文件时最大可用内存(MB)，当文件很大时提高此值也许可以提高生成速度。
                                 [default: 500]
  -g, --global_repeat_mode TEXT  全局重复模式，规则的重复模式未指定时使用此值:

                                 ? = 0次或1次
                                 * = 0次或多次
                                 [default: ?]
  -p, --part_size INTEGER        每个输出文件的最大占用大小(MB)，0表示不管数据量多大只输出到一个文件。
                                 [default: 0]
  -a, --append_mode INTEGER      是否将新输出的内容追加到OUTPUT中。
                                 [default: 0]
  -s, --seperator TEXT           单词分隔符，默认是当前平台的换行符，即一行一个密码。
                                 [default: Mac/Linux: \n, Windows: \r\n]
  --inencoding TEXT              字典文件编码，默认采用平台默认值。
  --outencoding TEXT             输出文件编码.  [default: utf-8]
  --help                         显示帮助信息。
```

输出文件默认采用 utf-8 编码，每个密码占一行，推荐使用*Notepad++*打开。

# 规则格式

**TTPassgen** 目前支持三种密码生成规则，以`--rule`选项指定，三种规则可以同时使用。

## CharArrayRule 字符数组规则

根据定义的字符数组及长度信息生成字符串。

规则格式：

```
[]{min_repeat:max_repeat:repeat_mode}
```

### 字符数组[]

使用 **[]** 包裹要生成密码的所有字符，会对这些字符进行排列组合。

内建字符集:

```
//小写字母列表
?l = abcdefghijklmnopqrstuvwxyz

//大写字母列表
?u = ABCDEFGHIJKLMNOPQRSTUVWXYZ

//数字列表
?d = 0123456789

//特殊字符列表
?s = !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~

//上面几个列表的集合
?a = ?l?u?d?s

//右方扣号，之所以单列出来是因为字符数组是用[]包裹的，如果字符数组中本身包含右方扣号的话就用此代替。
?q = ]
```

如 **[?d]** 表示从数字列表中选择。

### 定义重复模式

```
{min_repeat:max_repeat:repeat_mode}
```

对于字符数组规则而言，重复次数即是要生成的字符串的长度。

- `min_repeat` 最少重复次数
- `max_repeat` 最大重复次数
- `repeat_mode` 重复模式

采用类似正则表达式的风格定义规则：

**[]** 只出现 1 次。
`[123] -> 1 2 3`

**[]?** 0 次或 1 次。
`[123]? -> '' 1 2 3`

**[]{m:n:r}** 重复 m 到 n 次。重复模式(r)支持`?`或`*`。

- repeatMode 为 '?', 每个字符在生成的字符串中出现 0 次或 1 次。

  `[123]{1:2:?} -> 1 2 3 12 13 21 23 31 32`

- repeatMode 为 '\*', 每个字符在生成的字符串中出现 0 次或多次。

  `[123]{1:2:*} -> 1 2 3 11 12 13 21 22 23 31 32 33`

有如下规则简写方式：

- **[]{m:n}**

  等价于 `[]{m:m:global_repeat_mode}`

- **[]{n}**

  等价于 `[]{n:n:global_repeat_mode}`

- **[]{n:r}**

  等价于 `[]{n:n:r}`

### 示例

生成 8 位长度数字密码:

```
[?d]{8:8:*} or [?d]{8:*} or [1234567890]{8:8:*}
```

生成 8 位长度数字密码，密码中每个字符最多可出现一次。因为全局重复模式(global_repeat_mode)默认为'?'，所以重复模式可省略不写:

```
[?d]{8:8:?} or [?d]{8}
```

生成 7 到 8 位长度密码，密码可由大小写字母、数字和下划线组成:

```
[?l?u?d_]{7:8:*}
```

使用字符 1、2、3 生成 4 位长度密码，在每个密码中，每个字符最多可出现一次:

```
[123]{4}  //错误写法！密码长度不能大于字符的数目。
[123]{2}[123]{2}  //正确写法。
```

## StringArrayRule 字符串数组规则

根据定义的字符串列表及长度信息生成字符串。

规则格式：

- `$(string1,string2){min_repeat:max_repeat:repeat_mode}`

  字符串数组，每个字符串以逗号分割，不可有空格。

- `string`

  普通字符串，视为长度为 1 的字符串数组。

字符串数组规则定义与字符数组定义相同，字符串数组规则**不支持规则简写**。

### 示例

生成 8 位数字密码，以`abc`结尾:

```
[?d]{8:8:*}abc
```

从字符串列表(10,20,30)中选择一个数加在'age'后面:

```
age$(10,20,30){1:1:?}
```

同时使用字符数组规则与字符串数组规则，从字符串列表(10,20,30)中选择一个数加在'age'后面，密码以字母'a'或'b'结尾:

```
age$(10,20,30){1:1:?}[ab]
```

## DictRule 字典文件规则

从文件中读取字符串来组成密码，字典文件路径可由`--dictlist`选项来指定，例如`$0` 表示引用第 0 个字典文件的内容。
字典文件就是指普通的 txt 文件。

规则格式：

```
$index
```

字典文件规则不支持指定重复模式。

### 示例

`in.txt` 文件内容:

```
ab
cd
```

`in2.txt` 文件内容:

```
12
34
```

例如当`distlist`选项定义为 `in.dict,in2.dict`，指定单词分隔符为一个空格时，执行如下命令：

```bash
ttpassgen --dictlist "in.txt,in2.txt" --rule "$0[_]?$1" -s " " out.txt
```

输出:

```
ab12 ab34 ab_12 ab_34 cd12 cd34 cd_12 cd_34
```
