import sys
import os
import json
import logging

import pytest

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from configtree import logger
from configtree.script import ctdump


data_dir = os.path.dirname(os.path.realpath(__file__))
data_dir_with_conf = os.path.join(data_dir, "data", "script_with_conf")
data_dir_without_conf = os.path.join(data_dir, "data", "script_without_conf")
data_dir_invalid_conf = os.path.join(data_dir, "data", "script_invalid_conf")


@pytest.fixture(autouse=True)
def cleanup_env():
    path_len = len(sys.path)

    yield

    if len(sys.path) > path_len:
        sys.path.pop()
    try:
        del sys.modules["loaderconf"]
    except KeyError:
        pass
    os.environ.pop("ENV_NAME", None)
    for handler in logger.handlers[:]:
        if not isinstance(handler, logging.NullHandler):
            logger.removeHandler(handler)


def test_ctdump():
    argv = ["json", "-p", data_dir_with_conf]
    stdout = StringIO()
    ctdump(argv, stdout=stdout, stderr=False)
    stdout.seek(0)
    result = json.loads(stdout.read())
    assert result == {
        "database.driver": "mysql",
        "database.name": "devdb",
        "database.password": "qwerty",
        "database.user": "root",
        "http.host": "localhost",
        "http.port": 80,
    }


def test_ctdump_branch():
    argv = ["json", "-p", data_dir_with_conf, "-b", "http"]
    stdout = StringIO()
    ctdump(argv, stdout=stdout, stderr=False)
    stdout.seek(0)
    result = json.loads(stdout.read())
    assert result == {"host": "localhost", "port": 80}


def test_ctdump_invalid_branch():
    argv = ["json", "-p", data_dir_with_conf, "-b", "invalid"]
    stderr = StringIO()
    result = ctdump(argv, stderr=stderr)
    stderr.seek(0)
    assert result == 1
    assert "[ERROR]: Branch <invalid> does not exist" in stderr.read()


def test_ctdump_verbose():
    argv = ["json", "-p", data_dir_with_conf, "-v"]
    stderr = StringIO()
    ctdump(argv, stderr=stderr)
    stderr.seek(0)
    assert "[INFO]: Loading tree" in stderr.read()


def test_ctdump_processing_error():
    argv = ["json", "-p", data_dir_with_conf]
    os.environ["ENV_NAME"] = "prod"
    stderr = StringIO()
    result = ctdump(argv, stderr=stderr)
    stderr.seek(0)
    assert result == 1
    assert "[ERROR]: Undefined required key <http.host>" in stderr.read()


def test_ctdump_promise_error():
    argv = ["json", "-p", data_dir_with_conf]
    os.environ["ENV_NAME"] = "invalid"
    stderr = StringIO()
    result = ctdump(argv, stderr=stderr)
    stderr.seek(0)
    stderr = stderr.read()
    assert result == 1
    assert "[ERROR]: NameError: (" in stderr
    assert "<tree['http.host'] = '>>> invalid_expression()' from" in stderr


def test_ctdump_loaderconf_error():
    argv = ["json", "-p", data_dir_invalid_conf]
    stderr = StringIO()
    with pytest.raises(ValueError) as info:
        ctdump(argv, stderr=stderr)
    stderr.seek(0)
    assert info.value.args == ("Test",)
    assert (
        "[ERROR]: Failed to create loader.  Check your loaderconf.py" in stderr.read()
    )
