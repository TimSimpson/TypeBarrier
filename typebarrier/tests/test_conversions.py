import typing as t

import pytest

from typebarrier import conversions as c


NewTypeStr = t.NewType('NewTypeStr', str)


def test_primitives():
    assert c.convert_value(str, 'some-string') == 'some-string'
    assert c.convert_value(int, 42) == 42
    assert c.convert_value(bool, True)


def test_primitives_raises():
    with pytest.raises(TypeError) as excinfo:
        c.convert_value(str, 42)
    assert ('can\'t convert "42" (type <class \'int\'>) '
            'to <class \'str\'>' in str(excinfo.value))


def test_list():
    assert c.convert_value(list, [1, 2, '3']) == [1, 2, '3']
    assert c.convert_value(t.List[str], ['a', 'b']) == ['a', 'b']
    assert c.convert_value(list, range(5)) == [0, 1, 2, 3, 4]
    assert (c.convert_value(t.List[str], (str(x) for x in range(5)))
            == ['0', '1', '2', '3', '4'])


def test_list_failures():
    with pytest.raises(TypeError) as excinfo:
        c.convert_value(list, 42)
    assert ('can\'t convert "42" (type <class \'int\'>) '
            'to <class \'list\'>' in str(excinfo.value))

    with pytest.raises(TypeError) as excinfo:
        c.convert_value(t.List[str], [1, 2, 3])
    assert ('can\'t convert "[1, 2, 3]" (type <class \'list\'>) '
            'to typing.List[str].' in str(excinfo.value))


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

    def func0() -> str:
        return ':D'

    assert c.convert_list_to_kwargs(func0, []) == {}


def test_convert_list_arg():

    def some_func(s_list: t.List[str]) -> str:
        return ','.join(s_list)

    assert c.convert_value(some_func, ['a', 'b', 'c']) == 'a,b,c'

    # This is surprising, until you remember strings are iterable.
    # Cracking down on this might forbid useful behaviors, so in it stays.
    assert c.convert_value(some_func, 'a') == 'a'

    assert c.convert_value(some_func, 'abc') == 'a,b,c'

    with pytest.raises(TypeError) as excinfo:
        c.convert_value(some_func, 42)
    assert 'sole argument to' in str(excinfo.value)
    assert 'cannot be satisified with value 42' in str(excinfo.value)

    with pytest.raises(TypeError) as excinfo:
        c.convert_value(some_func, [42])
    assert 'sole argument to' in str(excinfo.value)
    assert 'cannot be satisified with value [42]' in str(excinfo.value)


def test_convert_list_arg_to_type_when_possible():

    class Guid:
        def __init__(self, name: str) -> None:
            self.name = name

        def __eq__(self, other):
            return isinstance(other, Guid) and self.name == other.name

    def some_func(g_list: t.List[Guid]) -> t.List[Guid]:
        return g_list

    expected_g_list = [Guid('a'), Guid('b'), Guid('c')]

    assert c.convert_value(some_func, expected_g_list) == expected_g_list

    a = c.convert_value(some_func, ['a', 'b', 'c'])
    assert a == expected_g_list


class Track:
    def __init__(self, name: str) -> None:
        self.name = name

    def __eq__(self, other):
        return isinstance(other, Track) and self.name == other.name

    def __repr__(self):
        return '~TRACK:' + self.name + '~'


class Disc:
    def __init__(self, tracks: t.List[Track]) -> None:
        self.tracks = tracks

    def __eq__(self, other):
        return isinstance(other, Disc) and self.tracks == other.tracks

    def __repr__(self):
        return 'DISC{' + ','.join(repr(track) for track in self.tracks) + '}'


MultiDiscAlbum = t.List[Disc]  # NOQA -it's a type stupid flake8


class TestConvertToListOfLists:
    expected_g_list = [
        Disc([
            Track('I Could Never Forget That Sandwhich'),
            Track('Someone Left a Bake Out Caked in Pain'),
            Track('Tim Simpson Fireside Chat, 1978'),
        ]),
        Disc([
            Track('Legend of Gaseous Duck'),
            Track('Greetings From the King of Crime'),
        ]),
    ]

    def test_convert_to_typed_list(self):
        actual = c.convert_value(
            Disc,
            [
                'I Could Never Forget That Sandwhich',
                'Someone Left a Bake Out Caked in Pain',
                'Tim Simpson Fireside Chat, 1978',
            ]
        )
        assert actual == self.expected_g_list[0]

    def test_convert_to_list_of_typed_list(self):
        actual = c.convert_value(
            MultiDiscAlbum,
            [
                [
                    'I Could Never Forget That Sandwhich',
                    'Someone Left a Bake Out Caked in Pain',
                    'Tim Simpson Fireside Chat, 1978',
                ],
                [
                    'Legend of Gaseous Duck',
                    'Greetings From the King of Crime',
                ]
            ])

        assert self.expected_g_list == actual
