from connection.success import test_connection_success as _success
from connection.success import test_connection_no_pages as _no_pages


def test_connection_success(capsys):
    _success(capsys)


def test_connection_no_pages(capsys):
    _no_pages(capsys)
