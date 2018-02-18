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
        raise TypeError('can\\'t convert "{arg1}" (type {type(arg1)}) to {cv1}.')
        """)  # NOQA
    assert g.namespace == {'cv1': str}


def test_int():
    g = cg.CodeGen()
    cg.convert_value(g, int, 'arg1')
    assert g.render() == code_str("""
        if issubclass(type(arg1), cv1):
            return arg1
        raise TypeError('can\\'t convert "{arg1}" (type {type(arg1)}) to {cv1}.')
        """)  # NOQA
    assert g.namespace == {'cv1': int}


def test_empty_callable():
    def func() -> int:
        return 1

    g = cg.CodeGen()
    cg.convert_value(g, func, 'arg1')
    assert g.render().startswith(code_str("""
        if isinstance(arg1, dict):
            raise NotImplemented()  # TODO: add dict code
        raise TypeError('<function test_empty_callable.<locals>"""))  # NOQA
    assert g.render().endswith(
        """does not accept any parameters, cannot convert from value {arg1}.')""")  # NOQA


def test_one_param_callable():
    def func(a: int) -> int:
        return 1

    g = cg.CodeGen()
    cg.convert_value(g, func, 'arg1')
    assert g.render() == code_str("""
        if isinstance(arg1, dict):
            raise NotImplemented()  # TODO: add dict code
        try:
            if issubclass(type(arg1), cv2):
                v1 = arg1
            raise TypeError('can\\'t convert "{arg1}" (type {type(arg1)}) to {cv2}.')
        except TypeError as v2:
            raise TypeError('sole argument to """ # NOQA
            + str(func) + """ accepts type <class 'int'>; cannot be satisified with value {arg1}.') from v2
        return cv1(v1)
    """)  # NOQA


def test_two_param_callable():
    def func(a: int, b: str) -> int:
        return 1

    g = cg.CodeGen()
    cg.convert_value(g, func, 'arg1')
    assert g.render().startswith(code_str("""
        if isinstance(arg1, dict):
            raise NotImplemented()  # TODO: add dict code
        raise TypeError("""))  # NOQA
    assert g.render().endswith(
        """accepts 2 parameters, cannot create from value "{arg1}".')""")  # NOQA
