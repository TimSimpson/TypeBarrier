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


# def test_call_func():

#     state = { 'called': False }

#     def func():
#         state['called'] = True

#     tb.typeify(func, None)
#     assert state['called']

#     state['called'] = False

#     tb.typeify(func, {})
#     assert state['called']


# def test_go():

#     def func(a: int, b: str="hai", **kwargs: t.Dict[str, int]) -> bool:
#         return False

#     tb.typeify(func, {'a': 4,  'b': 3})

#     assert False
