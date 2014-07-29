from os import path
from sys import version_info
from setuptools import setup


readme = ''.join(open(path.join(path.dirname(__file__), 'README.rst')))
requirements = ['pyyaml']

if version_info[0] == 2 and version_info[1] < 7:
    requirements.extend(['ordereddict', 'simplejson', 'argparse'])


setup(
    name='ConfigTree',
    version='0.1',
    description="",
    long_description=readme,
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='',
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
        bash = configtree.conv:to_bash

        [configtree.source]
        .json = configtree.source:load_json
        .yaml = configtree.source:load_yaml
        .yml = configtree.source:load_yaml
    """,
)
