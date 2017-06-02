from setuptools import setup, find_packages

classifiers=[
    # How mature is this project? Common values are
    #   3 - Alpha
    #   4 - Beta
    #   5 - Production/Stable
    'Development Status :: 5 - Production/Stable',

    # Indicate who your project is intended for
    # 'Intended Audience :: Developers',
    # 'Topic :: Software Development :: Build Tools',

    # Pick your license as you wish (should match "license" above)
     'License :: Apache License Version 2.0',

    # Specify the Python versions you support here. In particular, ensure
    # that you indicate whether you support Python 2, Python 3 or both.
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.2',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
]

long_description = ''
with open('README.rst') as f:
    long_description = f.read()

setup(
        name='ttpassgen',
        version='1.0',
        description='Highly flexiable and scriptable password dictionary generator.',
        author='tp7309',
        author_email='yiyou7309@gmail.com',
        url='https://github.com/tp7309/TTPassGen',
        license='Apache License Version 2.0',
        keywords='python ttpassgen password-generator wordlist password-dict password-dict-generator',
        long_description=long_description,
        packages=find_packages(),
        include_package_data=True,
        install_requires=[
            'click', 'tqdm'
        ],
        entry_points={
            'console_scripts':[
                'ttpassgen = ttpassgen.ttpassgen:cli',
            ],
        },
)


#pandoc --from=markdown --to=rst --output=README.rst README.md
#python setup.py register -r pypi
#python setup.py sdist upload -r pypi

#python setup.py bdist_wheel
#twine upload dist/*