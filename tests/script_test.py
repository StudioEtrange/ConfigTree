import sys
import os
import json
import logging
import warnings

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from nose import tools

from configtree import logger
from configtree.loader import ProcessingError
from configtree.script import ctdump, main


warnings.filterwarnings("ignore", module="configtree.loader")


data_dir = os.path.dirname(os.path.realpath(__file__))
data_dir_with_conf = os.path.join(data_dir, "data", "script_with_conf")
data_dir_without_conf = os.path.join(data_dir, "data", "script_without_conf")
data_dir_invalid_conf = os.path.join(data_dir, "data", "script_invalid_conf")


path_len = len(sys.path)


def teardown_func():
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


@tools.with_setup(teardown=teardown_func)
def ctdump_test():
    argv = ["json", "-p", data_dir_with_conf]
    stdout = StringIO()
    ctdump(argv, stdout=stdout, stderr=False)
    stdout.seek(0)
    result = json.loads(stdout.read())
    tools.eq_(
        result,
        {
            "database.driver": "mysql",
            "database.name": "devdb",
            "database.password": "qwerty",
            "database.user": "root",
            "http.host": "localhost",
            "http.port": 80,
        },
    )


@tools.with_setup(teardown=teardown_func)
def ctdump_branch_test():
    argv = ["json", "-p", data_dir_with_conf, "-b", "http"]
    stdout = StringIO()
    ctdump(argv, stdout=stdout, stderr=False)
    stdout.seek(0)
    result = json.loads(stdout.read())
    tools.eq_(result, {"host": "localhost", "port": 80})


@tools.with_setup(teardown=teardown_func)
def ctdump_invalid_branch_test():
    argv = ["json", "-p", data_dir_with_conf, "-b", "invalid"]
    stderr = StringIO()
    result = ctdump(argv, stderr=stderr)
    stderr.seek(0)
    tools.eq_(result, 1)
    tools.ok_("[ERROR]: Branch <invalid> does not exist" in stderr.read())


@tools.with_setup(teardown=teardown_func)
def ctdump_verbose_test():
    argv = ["json", "-p", data_dir_with_conf, "-v"]
    stderr = StringIO()
    ctdump(argv, stderr=stderr)
    stderr.seek(0)
    tools.ok_("[INFO]: Loading tree" in stderr.read())


@tools.with_setup(teardown=teardown_func)
def ctdump_processing_error_test():
    argv = ["json", "-p", data_dir_with_conf]
    os.environ["ENV_NAME"] = "prod"
    stderr = StringIO()
    result = ctdump(argv, stderr=stderr)
    stderr.seek(0)
    tools.eq_(result, 1)
    tools.ok_("[ERROR]: Undefined required key <http.host>" in stderr.read())


@tools.with_setup(teardown=teardown_func)
def ctdump_promise_error_test():
    argv = ["json", "-p", data_dir_with_conf]
    os.environ["ENV_NAME"] = "invalid"
    stderr = StringIO()
    result = ctdump(argv, stderr=stderr)
    stderr.seek(0)
    stderr = stderr.read()
    tools.eq_(result, 1)
    tools.ok_("[ERROR]: NameError: (" in stderr)
    tools.ok_("<tree['http.host'] = '>>> invalid_expression()' from" in stderr)


@tools.with_setup(teardown=teardown_func)
def ctdump_loaderconf_error_test():
    argv = ["json", "-p", data_dir_invalid_conf]
    stderr = StringIO()
    with tools.assert_raises(ValueError) as context:
        ctdump(argv, stderr=stderr)
    stderr.seek(0)
    tools.eq_(context.exception.args, ("Test",))
    tools.ok_(
        "[ERROR]: Failed to create loader.  Check your loaderconf.py" in stderr.read()
    )


###############################################################################
# Deprecated features
##


@tools.with_setup(teardown=teardown_func)
def configtree_stdout_test():
    argv = [data_dir_without_conf]
    main(argv, stderr=False)
    # Should not raise any exception


@tools.with_setup(teardown=teardown_func)
def configtree_without_conf_test():
    argv = [data_dir_without_conf]
    stdout = StringIO()
    main(argv, stdout=stdout, stderr=False)
    stdout.seek(0)
    result = stdout.read()
    result = [line.rstrip() for line in result.split(os.linesep)]
    tools.eq_(
        result,
        [
            "{",
            '    "database.driver": "mysql",',
            '    "database.name": "devdb",',
            '    "database.password": "qwerty",',
            '    "database.user": "root",',
            '    "http.host": null,',
            '    "http.port": 80',
            "}",
            "",
        ],
    )


@tools.with_setup(teardown=teardown_func)
def configtree_with_conf_test():
    argv = [data_dir_with_conf]
    stdout = StringIO()
    main(argv, stdout=stdout, stderr=False)
    stdout.seek(0)
    result = stdout.read()
    result = [line.rstrip() for line in result.split(os.linesep)]
    tools.eq_(
        result,
        [
            "{",
            '    "database.driver": "mysql",',
            '    "database.name": "devdb",',
            '    "database.password": "qwerty",',
            '    "database.user": "root",',
            '    "http.host": "localhost",',
            '    "http.port": 80',
            "}",
            "",
        ],
    )


@tools.with_setup(teardown=teardown_func)
def configtree_branch_test():
    argv = ["--branch=http", data_dir_with_conf]
    stdout = StringIO()
    main(argv, stdout=stdout, stderr=False)
    stdout.seek(0)
    result = stdout.read()
    result = [line.rstrip() for line in result.split(os.linesep)]
    tools.eq_(result, ["{", '    "host": "localhost",', '    "port": 80', "}", ""])


@tools.with_setup(teardown=teardown_func)
def configtree_format_test():
    argv = ["--format=shell", data_dir_with_conf]
    stdout = StringIO()
    main(argv, stdout=stdout, stderr=False)
    stdout.seek(0)
    result = stdout.read()
    result = [line.rstrip() for line in result.split(os.linesep)]
    tools.eq_(
        result,
        [
            "DATABASE_DRIVER='mysql'",
            "DATABASE_NAME='devdb'",
            "DATABASE_PASSWORD='qwerty'",
            "DATABASE_USER='root'",
            "HTTP_HOST='localhost'",
            "HTTP_PORT='80'",
            "",
        ],
    )


@tools.raises(ValueError)
@tools.with_setup(teardown=teardown_func)
def configtree_invalid_format_test():
    argv = ["--format=invalid", data_dir_with_conf]
    main(argv, stderr=False)


@tools.with_setup(teardown=teardown_func)
def configtree_postprocess_test():
    os.environ["ENV_NAME"] = "prod"
    argv = [data_dir_with_conf]
    with tools.assert_raises(ProcessingError) as context:
        main(argv, stderr=False)
    tools.eq_(context.exception.args[0].key, "http.host")
