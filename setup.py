from os import path
from sys import version_info
from setuptools import setup


with open(path.join(path.dirname(__file__), 'README.rst')) as f:
    readme = f.read()

with open(path.join(path.dirname(__file__), 'CHANGES.rst')) as f:
    readme += '\n\n' + f.read()

requirements = ['pyyaml']
if version_info[0] == 2 and version_info[1] < 7:
    requirements.extend(['ordereddict', 'simplejson', 'argparse'])


setup(
    name='ConfigTree',
    version='0.2',
    description='Is a configuration management tool',
    long_description=readme,
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
    ],
    keywords='configuration config settings tree',
    author='Dmitry Vakhrushev',
    author_email='self@kr41.net',
    url='https://bitbucket.org/kr41/configtree',
    download_url='https://bitbucket.org/kr41/configtree/downloads',
    license='BSD',
    packages=['configtree'],
    install_requires=requirements,
    include_package_data=True,
    zip_safe=True,
    entry_points="""\
        [console_scripts]
        configtree = configtree.script:main

        [configtree.conv]
        json = configtree.conv:to_json
        rare_json = configtree.conv:to_rare_json
        shell = configtree.conv:to_shell

        [configtree.source]
        .json = configtree.source:from_json
        .yaml = configtree.source:from_yaml
        .yml = configtree.source:from_yaml
    """,
)
