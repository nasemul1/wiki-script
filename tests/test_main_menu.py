from main_menu.success import test_menu_exit as _exit
from main_menu.success import test_menu_invalid_option as _invalid
from main_menu.success import test_menu_dispatches_handler as _dispatch
from main_menu.success import test_menu_handles_error as _error


def test_menu_exit(capsys):
    _exit(capsys)


def test_menu_invalid_option(capsys):
    _invalid(capsys)


def test_menu_dispatches_handler(capsys):
    _dispatch(capsys)


def test_menu_handles_error(capsys):
    _error(capsys)
