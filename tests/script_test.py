import sys
import os
import warnings
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from nose import tools

from configtree.loader import ProcessingError
from configtree.script import main


warnings.filterwarnings('ignore', module='configtree.loader')


data_dir = os.path.dirname(os.path.realpath(__file__))
data_dir_with_conf = os.path.join(data_dir, 'data', 'script_with_conf')
data_dir_without_conf = os.path.join(data_dir, 'data', 'script_without_conf')


def teardown_func():
    try:
        sys.path.remove(data_dir_with_conf)
    except ValueError:
        pass
    try:
        del sys.modules['loaderconf']
    except KeyError:
        pass


@tools.with_setup(teardown=teardown_func)
def stdout_test():
    argv = [data_dir_without_conf]
    main(argv, stderr=False)
    # Should not raise any exception


@tools.with_setup(teardown=teardown_func)
def without_conf_test():
    argv = [data_dir_without_conf]
    stdout = StringIO()
    main(argv, stdout=stdout, stderr=False)
    stdout.seek(0)
    result = stdout.read()
    result = [line.rstrip() for line in result.split(os.linesep)]
    tools.eq_(result, [
        '{',
        '    "database.driver": "mysql",',
        '    "database.name": "devdb",',
        '    "database.password": "qwerty",',
        '    "database.user": "root",',
        '    "http.host": null,',
        '    "http.port": 80',
        '}',
        '',
    ])


@tools.with_setup(teardown=teardown_func)
def with_conf_test():
    argv = [data_dir_with_conf]
    stdout = StringIO()
    main(argv, stdout=stdout, stderr=False)
    stdout.seek(0)
    result = stdout.read()
    result = [line.rstrip() for line in result.split(os.linesep)]
    tools.eq_(result, [
        '{',
        '    "database.driver": "mysql",',
        '    "database.name": "devdb",',
        '    "database.password": "qwerty",',
        '    "database.user": "root",',
        '    "http.host": "localhost",',
        '    "http.port": 80',
        '}',
        '',
    ])


@tools.with_setup(teardown=teardown_func)
def branch_test():
    argv = ['--branch=http', data_dir_with_conf]
    stdout = StringIO()
    main(argv, stdout=stdout, stderr=False)
    stdout.seek(0)
    result = stdout.read()
    result = [line.rstrip() for line in result.split(os.linesep)]
    tools.eq_(result, [
        '{',
        '    "host": "localhost",',
        '    "port": 80',
        '}',
        '',
    ])


@tools.with_setup(teardown=teardown_func)
def format_test():
    argv = ['--format=shell', data_dir_with_conf]
    stdout = StringIO()
    main(argv, stdout=stdout, stderr=False)
    stdout.seek(0)
    result = stdout.read()
    result = [line.rstrip() for line in result.split(os.linesep)]
    tools.eq_(result, [
        "DATABASE_DRIVER='mysql'",
        "DATABASE_NAME='devdb'",
        "DATABASE_PASSWORD='qwerty'",
        "DATABASE_USER='root'",
        "HTTP_HOST='localhost'",
        "HTTP_PORT='80'",
        "",
    ])


@tools.raises(ValueError)
@tools.with_setup(teardown=teardown_func)
def invalid_format_test():
    argv = ['--format=invalid', data_dir_with_conf]
    main(argv, stderr=False)


@tools.with_setup(teardown=teardown_func)
def postprocess_test():
    os.environ['ENV_NAME'] = 'prod'
    argv = [data_dir_with_conf]
    with tools.assert_raises(ProcessingError) as context:
        main(argv, stderr=False)
    tools.eq_(context.exception.args[0].key, 'http.host')
