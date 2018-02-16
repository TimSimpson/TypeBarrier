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


def test_invalid_conversions():
    def some_func() -> int:
        return 42

    with pytest.raises(TypeError) as excinfo:
        c.convert_value(some_func, 42)

    assert 'does not accept any parameters,' in str(excinfo.value)


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


def test_convert_list_to_kwargs():

    def func(a: int, b: str) -> str:
        return f'a={a}, b={b}'

    assert c.convert_list_to_kwargs(func, [1, 'a']) == {'a': 1, 'b': 'a'}

    def func2(a: int, b: str, c: bool=False) -> str:
        return f'a={a}, b={b}, c={c}'

    assert c.convert_list_to_kwargs(func2, [1, 'a', True]) == {
        'a': 1, 'b': 'a', 'c': True}

    assert c.convert_list_to_kwargs(func2, [1, 'a']) == {
        'a': 1, 'b': 'a'}

    with pytest.raises(TypeError) as excinfo:
        c.convert_list_to_kwargs(func2, [1])

    assert 'missing a positional argument: 1' in str(excinfo.value)

    def func3(*args) -> str:
        return ' '.join(args)

    assert c.convert_list_to_kwargs(func3, []) == {'args': []}

    assert c.convert_list_to_kwargs(func3, [1, 2, 3]) == {'args': [1, 2, 3]}

    def func4(*args: str) -> str:
        return ' '.join(args)

    assert c.convert_list_to_kwargs(func4, []) == {'args': []}

    with pytest.raises(TypeError) as excinfo:
        c.convert_list_to_kwargs(func4, [1, 2, 3])

    assert ('problem converting element 0 in a list of args for '
            in str(excinfo.value))
