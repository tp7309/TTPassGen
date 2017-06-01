from setuptools import setup, find_packages

setup(
        name='TTPassGen',
        version='1.0',
        packages=find_packages(),
        include_package_data=True,
        entry_points='''
            [console_scripts]
            TTPassGen=TTPassGen:cli
        ''',
)
