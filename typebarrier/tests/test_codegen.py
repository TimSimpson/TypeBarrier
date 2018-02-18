import typing as t

from typebarrier import codegen as cg


def test_noop():
    g = cg.CodeGen()
    cg.convert_value(g, t.Any, 'arg1')
    assert g.render() == """return arg1"""


def test_str():
    g = cg.CodeGen()
    cg.convert_value(g, str, 'arg1')
    assert g.render() == """return arg1"""
