from setuptools import setup, find_packages

setup(
        name='ttpassgen',
        version='0.0.4',
        description='Highly flexiable and scriptable password dictionary generator',
        author='tp7309',
        author_email='yiyou7309@gmail.com',
        url='https://github.com/tp7309/TTPassGen',
        license='LICENSE',
        keywords='python ttpassgen password-generator wordlist password-dict password-dict-generator',
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