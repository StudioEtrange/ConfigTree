from os import path
from setuptools import setup, find_packages


with open(path.join(path.dirname(__file__), "README.rst")) as f:
    readme = f.read()

with open(path.join(path.dirname(__file__), "CHANGES.rst")) as f:
    readme += "\n\n" + f.read()

with open(path.join(path.dirname(__file__), "configtree", "__init__.py")) as f:
    version = next(line for line in f if line.startswith("__version__"))
    version = version.strip().split(" = ")[1]
    version = version.strip('"')

setup(
    name="ConfigTree",
    version=version,
    description="Is a configuration management tool",
    long_description=readme,
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
    ],
    keywords="configuration config settings tree",
    url="https://github.com/Cottonwood-Technology/ConfigTree",
    author="Cottonwood Technology",
    author_email="info@cottonwood.tech",
    license="BSD",
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=["pyyaml", "cached-property"],
    include_package_data=True,
    zip_safe=True,
    entry_points="""\
        [console_scripts]
        ctdump = configtree.script:ctdump

        [configtree.formatter]
        json = configtree.formatter:to_json
        shell = configtree.formatter:to_shell

        [configtree.source]
        .json = configtree.source:from_json
        .yaml = configtree.source:from_yaml
        .yml = configtree.source:from_yaml
    """,
)
