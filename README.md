#TTPassGen
TTPassGen is a highly flexiable and scriptable password dictionary generator base on Python, you can easily use various rules to generate the desired combination of words.

#Features
- generate password use combination、permulation、conditional rules and so on.
- support all characters or words(from wordlist file) that can make up a password, some built-in charset has been provided, such as alphabetical lists and numeric lists.
- you can specify the order and frequency of each element in the word.
- simple rule format, and easy to use, rule could be defined similar some regex's style.
- time-consuming estimates, output size estimates, and real-time progress reports.
- unicode word support by using wordlist file as input.
- Generation of large amounts of passwords at once, no size limit.
- it can breakup output by file size.

#Install
`TTPassGen` can be easily installed using pip:
```
pip install ttpassgen
```

#Requirements
Python 2 (version 2.7 or later), or Python 3 (version 3.2 or later).

#Quick Start
> Switch to the project's `src` directory if you downloaded the source code.
Example: Generate word list output to file, the word format is prefix three digits, range 123, appear 2 to 3 times, followed by letter a or b.
```
ttpassgen -r [123]{2:3}[ab] out.dict
```
Done.

#Options
```
C:\Users\tp730>ttpassgen --help
Usage: ttpassgen [OPTIONS] OUTPUT
Options:
  -m, --mode INTEGER             generation mode:

                                 0 = combination rule mode
                                 [default: 0]
  -d, --dictlist TEXT            read wordlist from the file, multi files
                                 should by seperated by comma.
  -r, --rule TEXT                define word format, {0} means refer first
                                 file in wordlist, some built-in charsets:

                                 ?l
                                 = abcdefghijklmnopqrstuvwxyz
                                 ?u =
                                 ABCDEFGHIJKLMNOPQRSTUVWXYZ
                                 ?d = 0123456789
                                 ?s
                                 = !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
                                 ?a =
                                 ?l?u?d?s
                                 ?q = ]

                                 example: [?dA]{1:2}{0}
                                 view
                                 documentation for more information.
                                 [default: ]
  -c, --dict_cache INTEGER       each element in 'dictlist' option represents
                                 a dict file path, this option define the
                                 maximum amount of memory(MB) that can be used
                                 when reading their contents.increasing the
                                 cache may speed up the build when input dict
                                 files is huge.  [default: 500]
  -g, --global_repeat_mode TEXT  whether the character is allowd to repeat:

                                 ?
                                 = 0 or 1 repetitions
                                 * = 0 or more
                                 repetitions  [default: ?]
  -p, --part_size INTEGER        when result data is huge, split package
                                 size(MB) will be applied, 0 is unlimited.
                                 [default: 0]
  --help                         Show this message and exit.
```
Writting...

