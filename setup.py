from os import path
from setuptools import setup


with open(path.join(path.dirname(__file__), 'README.rst')) as f:
    readme = f.read()

with open(path.join(path.dirname(__file__), 'CHANGES.rst')) as f:
    readme += '\n\n' + f.read()


setup(
    name='ConfigTree',
    version='0.5.1',
    description='Is a configuration management tool',
    long_description=readme,
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
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
    install_requires=['pyyaml', 'cached-property'],
    include_package_data=True,
    zip_safe=True,
    entry_points="""\
        [console_scripts]
        configtree = configtree.script:main
        ctdump = configtree.script:ctdump

        [configtree.conv]
        json = configtree.conv:to_json
        rare_json = configtree.conv:to_rare_json
        shell = configtree.conv:to_shell

        [configtree.formatter]
        json = configtree.formatter:to_json
        shell = configtree.formatter:to_shell

        [configtree.source]
        .json = configtree.source:from_json
        .yaml = configtree.source:from_yaml
        .yml = configtree.source:from_yaml
    """,
)
