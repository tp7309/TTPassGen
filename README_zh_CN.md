# TTPassGen
[![Build Status](https://travis-ci.org/tp7309/TTPassGen.svg?branch=master)](https://travis-ci.org/tp7309/TTPassGen)
[![Coverage Status](https://coveralls.io/repos/github/tp7309/TTPassGen/badge.svg?branch=master)](https://coveralls.io/github/tp7309/TTPassGen?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/25f05aa766c34eea9b9692725237e873)](https://www.codacy.com/app/tp7309/TTPassGen?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=tp7309/TTPassGen&amp;utm_campaign=Badge_Grade)

TTPassGen是一个支持灵活定制的密码字典生成器，我们可以轻松地定义各种规则来生成所需的单词组合。因为基于Python，所以可以跨平台使用。

# 特性
- 使用组合，排列，条件规则等生成密码。
- 支持可以组成密码的所有字符或单词（从wordlist选项中获取输入字典路径），还提供了一些内置的字符集，例如字母列表和数字列表。
- 可以指定单词中每个元素出现的顺序和频率。
- 规则格式非常容易学习，程序易于使用，规则定义采用类似于正则表达式的风格。
- 提供生成密码词典的耗时预估，输出文件大小预估和实时进度报告。
- 使用wordlist选项可以支持中文之类的unicode字符组成密码。
- 可以一次生成大量密码，无输出大小限制。
- 支持通过设置每个输出字典的大小来将数据输出到多个文件，防止单个字典过大。

# 安装
`TTPassGen` 可以使用Python的`pip`轻松安装:
```
pip install ttpassgen
```
如果你使用的是Windows操作系统，可以直接下载[release version](https://github.com/tp7309/TTPassGen/releases)，这样就不需要Python环境了。

# 使用要求
Python 2 (version 2.7 or later), or Python 3 (version 3.3 or later).
如果你使用的是Windows操作系统，不需要Python环境，也可以直接下载[release version](https://github.com/tp7309/TTPassGen/releases)。

# 快速使用
> 如何你要使用源码的话，在终端或命令提示符窗口中先切换ttpassgen目录下，下面有ttpassgen.py，如果是是使用ttpassgen.exe文件，那么注意最好在Windows的命令提示符窗口下执行命令。

示例：生成单词列表输出到文件out.dict，单词格式为最前面是三个数字，只允许1、2、3，出现2或3次，后跟字母a或b。
```
ttpassgen -r [123]{2:3}[ab] out.dict
```
可以打开out.dict查看结果（建议用Notepad++打开）。

# 配置项
```
C:\Users\tp730>ttpassgen --help
Usage: ttpassgen [OPTIONS] OUTPUT
Options:
  -m, --mode INTEGER             指定生成模式:

                                 0 = 规则定义模式
                                 [默认值: 0]
  -d, --dictlist TEXT            定义在要--rule选项引用的字典文件路径， 
                                 有多个路径的话用逗号出来隔开。
                                 
  -r, --rule TEXT                定义用于生成的密码的规则, $0 意思指定引用--dictlist选项中的第0个文件, 内建字符集:

                                 ?l = abcdefghijklmnopqrstuvwxyz
                                 ?u = ABCDEFGHIJKLMNOPQRSTUVWXYZ
                                 ?d = 0123456789
                                 ?s = !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
                                 ?a = ?l?u?d?s
                                 ?q = ]

                                 示例: [?dA]{1:2}$0
                                 查看*Examples*节以了解更多信息.
                                 [默认值: ]
  -c, --dict_cache INTEGER       读取--dictlist选项中文件时最大可用内存(MB)，当文件很大时提高此值也许可能提高生成速度。
                                 [default: 500]
  -g, --global_repeat_mode TEXT  全局重复模式:

                                 ? = 0次或1次
                                 * = 0次或多次
                                 [default: ?]
  -p, --part_size INTEGER        每个输出文件的最大占用大小(MB)，0表示不管数据量多大只输出到一个文件。
                                 [default: 0]
  -a, --append_mode INTEGER      是否将新输出的内容填加到OUTPUT中。
                                 [default: 0]
  -s, --seperator TEXT           单词分隔符，默认是当前平台的换行符，特殊换行符：

                                 &#160; = 一个空格
                                 [default: ]
  --help                         显示帮助信息。
```
输出文件采用utf-8编码，每个密码占一行，推荐使用Notepad++打开。

# 示例
**[]**  一对方括号用于包裹所有要使用的字符。

## 定义重复模式
**[]**  只出现1次。
`[123] -> 1 2 3`

**[]?** 0次或1次。
`[123] -> '' 1 2 3`

**[]{m:n:r}**  重复m次到n次，重复模式(r)支持`?`或`*`。
```
repeatMode为 `?`, [123]{1,2:?} -> 1 2 3 12 13 21 23 31 32
repeatMode为 `*`, [123]{1,2:*} -> 1 2 3 11 12 13 21 22 23 31 32 33
```

**[]{m:n}** 重复m次到n次，重复模式未定义时采用`global_repeat_mode`选项定义的值。

**[]{n} or []{n:r}**
相当于`[]{n:n:r}`.

**$no** 引用`dictlist`选项中的输入文件的内容。
```
ttpassgen --dictlist in.dict,in2.dict --rule $0[_]?$1 -s "&#160;" out.dict
例如当`distlist`选项定义为 `in.dict,in2.dict` 时，
in.dict文件内容:
word11
word12

in2.dict文件内容:
word21
word22


输出：
word11word21 word11word22 word11_word21 word11_word22 word12word21 word12word22 word12_word21 word12_word22
```

# 更新日志
[更新日志](https://github.com/tp7309/TTPassGen/blob/master/CHANGES.md)