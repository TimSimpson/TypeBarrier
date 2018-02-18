import typing as t

from typebarrier import inline as i


def test_convert_list():
    converter = i.convert_list(t.List[str])
    assert converter('123') == ['1', '2', '3']
