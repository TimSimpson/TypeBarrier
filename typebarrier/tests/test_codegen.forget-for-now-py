import textwrap
import typing as t

from typebarrier import codegen as cg


def code_str(txt):
    # stip extra lines on both sides of overall input,
    # then strip right side of each line
    return '\n'.join(line.rstrip()
                     for line in textwrap.dedent(txt).strip().split('\n'))


def test_noop():
    g = cg.CodeGen()
    cg.convert_value(g, t.Any, 'arg1')
    assert g.render() == """return arg1"""


def test_str():
    g = cg.CodeGen()
    cg.convert_value(g, str, 'arg1')
    assert g.render() == code_str("""
        if issubclass(type(arg1), cv1):
            return arg1
        else:
            raise TypeError(f'can\\'t convert "{arg1}" (type {type(arg1)}) to {cv1}.')
        """)  # NOQA
    assert g.namespace == {'cv1': str}


def test_int():
    g = cg.CodeGen()
    cg.convert_value(g, int, 'arg1')
    assert g.render() == code_str("""
        if issubclass(type(arg1), cv1):
            return arg1
        else:
            raise TypeError(f'can\\'t convert "{arg1}" (type {type(arg1)}) to {cv1}.')
        """)  # NOQA
    assert g.namespace == {'cv1': int}


def test_empty_callable():
    def func() -> int:
        return 1

    g = cg.CodeGen()
    cg.convert_value(g, func, 'arg1')

    expected = code_str("""
        if isinstance(arg1, dict):
            v2 = {}
            v3 = set()
            v4 = set(arg1.keys()).difference(v3)
            if v4:
                raise TypeError(f'the following parameters not accepted for "%FUNC%" : {list(v4)}')
                v1 = v2
            return cv1(**v1)
        else:
            raise TypeError(f'%FUNC% does not accept any parameters, cannot convert from value {arg1}.')
        """)  # NOQA
    expected = expected.replace('%FUNC%', str(func))

    assert g.render() == expected
    assert g.namespace == {'cv1': func}


def test_one_param_callable():
    def func(a: int) -> int:
        return 1

    g = cg.CodeGen()
    cg.convert_value(g, func, 'arg1')

    expected = code_str("""
        if isinstance(arg1, dict):
            v2 = {}
            try:
                if issubclass(type(arg1["a"]), cv2):
                    v2["a"] = arg1["a"]
                else:
                    raise TypeError(f'can\\'t convert "{arg1["a"]}" (type {type(arg1["a"])}) to {cv2}.')
            except KeyError as v3:
                raise TypeError(f'missing a required argument: {v3}') from v3
            v4 = set('a')
            v5 = set(arg1.keys()).difference(v4)
            if v5:
                raise TypeError(f'the following parameters not accepted for "%ADDRESS%" : {list(v5)}')
                v1 = v2
            return cv1(**v1)
        else:
            try:
                if issubclass(type(arg1), cv2):
                    v6 = arg1
                else:
                    raise TypeError(f'can\\'t convert "{arg1}" (type {type(arg1)}) to {cv2}.')
            except TypeError as v7:
                raise TypeError(f'sole argument to %ADDRESS% accepts type <class \\'int\\'>; cannot be satisified with value {arg1}.') from v7
            return cv1(v6)
    """)  # NOQA
    expected = expected.replace('%ADDRESS%', str(func))
    assert g.render() == expected
    assert g.namespace == {'cv1': func, 'cv2': int}


def test_two_param_callable():
    def func(a: int, b: str) -> int:
        return 1

    g = cg.CodeGen()
    cg.convert_value(g, func, 'arg1')

    print(g.render())
    expected = code_str("""
        if isinstance(arg1, dict):
            v2 = {}
            try:
                if issubclass(type(arg1["a"]), cv2):
                    v2["a"] = arg1["a"]
                else:
                    raise TypeError(f'can\\'t convert "{arg1["a"]}" (type {type(arg1["a"])}) to {cv2}.')
                if issubclass(type(arg1["b"]), cv3):
                    v2["b"] = arg1["b"]
                else:
                    raise TypeError(f'can\\'t convert "{arg1["b"]}" (type {type(arg1["b"])}) to {cv3}.')
            except KeyError as v3:
                raise TypeError(f'missing a required argument: {v3}') from v3
            v4 = set('a','b')
            v5 = set(arg1.keys()).difference(v4)
            if v5:
                raise TypeError(f'the following parameters not accepted for "%ADDRESS%" : {list(v5)}')
                v1 = v2
            return cv1(**v1)
        else:
            raise TypeError(f'%ADDRESS% accepts 2 parameters, cannot create from value "{arg1}".')
    """)  # NOQA
    expected = expected.replace('%ADDRESS%', str(func))

    assert g.render() == expected
    assert g.namespace == {'cv1': func, 'cv2': int, 'cv3': str}
