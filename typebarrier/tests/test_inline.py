import typing as t

import pytest

from typebarrier import inline as i


def test_convert_list():
    converter = i.convert_list(t.List[str])
    assert converter('123') == ['1', '2', '3']


def test_noop():
    to_any = i.convert_value(t.Any)

    class Blah:
        pass

    b = Blah()
    assert to_any(b) is b


def test_one_param_callable():
    def func(a: int) -> int:
        return a + 10

    to_func = i.convert_value(func)
    assert to_func(2) == 12

    with pytest.raises(TypeError) as excinfo:
        to_func('2')

    assert ('sole argument to '
            in str(excinfo.value))
    assert ('accepts type <class \'int\'>; cannot be satisified with value 2'
            in str(excinfo.value))
