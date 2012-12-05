from os import path
from setuptools import setup

readme = ''.join(open(path.join(path.dirname(__file__), 'README.rst')))

import configtree

setup(
    name='ConfigTree',
    version=configtree.__version__,
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
    entry_points={
        'configtree.parsers': (
            '.json = json:load',
            '.yaml = yaml:load',
        ),
    },
    include_package_data=True,
    zip_safe=True,
)
