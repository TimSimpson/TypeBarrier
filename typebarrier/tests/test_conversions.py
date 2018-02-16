import typing as t

import pytest

from typebarrier import conversions as c


NewTypeStr = t.NewType('NewTypeStr', str)


def test_primitives():
    assert c.convert_value(str, 'some-string') == 'some-string'
    assert c.convert_value(int, 42) == 42
    assert c.convert_value(bool, True)

    with pytest.raises(TypeError) as excinfo:
        c.convert_value(str, 42)
    assert ('can\'t convert "42" (type <class \'int\'>) '
            'to <class \'str\'>' in str(excinfo.value))


def test_new_type():
    assert c.convert_value(NewTypeStr, 'some-string') == 'some-string'


def test_single_arg_func():

    def some_func(i: int) -> str:
        return f'index={i}'

    assert c.convert_value(some_func, 78) == 'index=78'


def test_single_arg_func_from_wrong_type_fails():

    def some_func(i: int) -> str:
        return f'index={i}'

    with pytest.raises(TypeError) as excinfo:
        c.convert_value(some_func, 'hai')

    assert ('accepts type <class \'int\'>; cannot be satisified'
            in str(excinfo.value))


def test_single_arg_class_init():
    class Guid:
        def __init__(self, value: str) -> None:
            self.value = value

    guid = c.convert_value(Guid, 'happy')
    assert guid.value == 'happy'


def test_single_arg_class_init_from_wrong_type_fails():

    class Guid:
        def __init__(self, value: str) -> None:
            self.value = value

    with pytest.raises(TypeError) as excinfo:
        c.convert_value(Guid, 42)

    assert ('accepts type <class \'str\'>; cannot be satisified'
            in str(excinfo.value))


def test_two_arg_func():

    def some_func(a: int, b: int) -> str:
        return f'index={a}'

    with pytest.raises(TypeError) as excinfo:
        c.convert_value(some_func, 78)

    assert 'accepts 2 parameters, cannot create' in str(excinfo.value)
