import typing as t

import pytest

from typebarrier import dynamic as d


# This decorator
# Define a lot of types for the tests to play with.

NewTypeStr = t.NewType('NewTypeStr', str)


class Guid:
    def __init__(self, value: str) -> None:
        self.value = value

    def __eq__(self, other):
        return isinstance(other, Guid) and self.value == other.value

    def __hash__(self):
        return hash(self.value)


class Track:
    def __init__(self, name: str) -> None:
        self.name = name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, Track) and self.name == other.name

    def __repr__(self):
        return '~TRACK:' + self.name + '~'


Artist = t.NewType('Artist', str)


class Disc:
    def __init__(self, tracks: t.List[Track]) -> None:
        self.tracks = tracks

    def __eq__(self, other):
        return isinstance(other, Disc) and self.tracks == other.tracks

    def __repr__(self):
        return 'DISC{' + ','.join(repr(track) for track in self.tracks) + '}'


MultiDiscAlbum = t.List[Disc]  # NOQA -it's a type stupid flake8


TrackToArtistMapping = t.Dict[Track, Artist]


def test_primitives():
    assert d.convert_value(str, 'some-string') == 'some-string'
    assert d.convert_value(int, 42) == 42
    assert d.convert_value(bool, True)


def test_primitives_raises():
    with pytest.raises(TypeError) as excinfo:
        d.convert_value(str, 42)
    assert ('can\'t convert "42" (type <class \'int\'>) '
            'to <class \'str\'>' in str(excinfo.value))


def test_list():
    assert d.convert_value(list, [1, 2, '3']) == [1, 2, '3']
    assert d.convert_value(t.List[str], ['a', 'b']) == ['a', 'b']
    assert d.convert_value(list, range(5)) == [0, 1, 2, 3, 4]
    assert (d.convert_value(t.List[str], (str(x) for x in range(5)))
            == ['0', '1', '2', '3', '4'])


def test_list_failures():
    with pytest.raises(TypeError) as excinfo:
        d.convert_value(list, 42)
    assert ('can\'t convert "42" (type <class \'int\'>) '
            'to <class \'list\'>' in str(excinfo.value))

    with pytest.raises(TypeError) as excinfo:
        d.convert_value(t.List[str], [1, 2, 3])
    assert ('can\'t convert "[1, 2, 3]" (type <class \'list\'>) '
            'to typing.List[str].' in str(excinfo.value))


def test_dictionary():
    assert d.convert_value(dict, {'a': 1, 2: 'b'}) == {'a': 1, 2: 'b'}
    assert (d.convert_value(t.Dict[str, int], {'a': 1, 'b': 2})
            == {'a': 1, 'b': 2})


def test_dictionary_failures():
    with pytest.raises(TypeError) as excinfo:
        d.convert_value(dict, 42)
    assert ('can\'t convert "42" (type <class \'int\'>) '
            'to <class \'dict\'>' in str(excinfo.value))

    with pytest.raises(TypeError) as excinfo:
        d.convert_value(t.Dict[str, int], {1: 1})
    assert ('can\'t convert "{1: 1}" (type <class \'dict\'>) '
            'to typing.Dict[str, int].' in str(excinfo.value))

    with pytest.raises(TypeError) as excinfo:
        d.convert_value(t.Dict[str, int], {'a': 'b'})
    assert ('can\'t convert "{\'a\': \'b\'}" (type <class \'dict\'>) '
            'to typing.Dict[str, int].' in str(excinfo.value))


def test_new_type():
    assert d.convert_value(NewTypeStr, 'some-string') == 'some-string'


def test_invalid_conversions():
    def some_func() -> int:
        return 42

    with pytest.raises(TypeError) as excinfo:
        d.convert_value(some_func, 42)

    assert 'does not accept any parameters,' in str(excinfo.value)


def test_single_arg_func():

    def some_func(i: int) -> str:
        return f'index={i}'

    assert d.convert_value(some_func, 78) == 'index=78'


def test_single_arg_func_from_wrong_type_fails():

    def some_func(i: int) -> str:
        return f'index={i}'

    with pytest.raises(TypeError) as excinfo:
        d.convert_value(some_func, 'hai')

    assert ('accepts type <class \'int\'>; cannot be satisified'
            in str(excinfo.value))


def test_single_arg_class_init():

    guid = d.convert_value(Guid, 'happy')
    assert guid.value == 'happy'


def test_single_arg_class_init_from_wrong_type_fails():

    class Guid:
        def __init__(self, value: str) -> None:
            self.value = value

    with pytest.raises(TypeError) as excinfo:
        d.convert_value(Guid, 42)

    assert ('accepts type <class \'str\'>; cannot be satisified'
            in str(excinfo.value))


def test_two_arg_func():

    def some_func(a: int, b: int) -> str:
        return f'index={a}'

    with pytest.raises(TypeError) as excinfo:
        d.convert_value(some_func, 78)

    assert 'accepts 2 parameters, cannot create' in str(excinfo.value)


def test_convert_list_to_kwargs():

    def func(a: int, b: str) -> str:
        return f'a={a}, b={b}'

    assert d.convert_list_to_kwargs(func, [1, 'a']) == {'a': 1, 'b': 'a'}

    def func2(a: int, b: str, c: bool=False) -> str:
        return f'a={a}, b={b}, c={c}'

    assert d.convert_list_to_kwargs(func2, [1, 'a', True]) == {
        'a': 1, 'b': 'a', 'c': True}

    assert d.convert_list_to_kwargs(func2, [1, 'a']) == {
        'a': 1, 'b': 'a'}

    with pytest.raises(TypeError) as excinfo:
        d.convert_list_to_kwargs(func2, [1])

    with pytest.raises(TypeError) as excinfo:
        d.convert_list_to_kwargs(func2, [1, 'a', True, 4])

    assert '3 positional argument(s) but 4 were given' in str(excinfo.value)

    def func3(*args) -> str:
        return ' '.join(args)

    assert d.convert_list_to_kwargs(func3, []) == {'args': []}

    assert d.convert_list_to_kwargs(func3, [1, 2, 3]) == {'args': [1, 2, 3]}

    def func4(*args: str) -> str:
        return ' '.join(args)

    assert d.convert_list_to_kwargs(func4, []) == {'args': []}

    with pytest.raises(TypeError) as excinfo:
        d.convert_list_to_kwargs(func4, [1, 2, 3])

    assert ('problem converting element 0 in a list of args for '
            in str(excinfo.value))

    def func0() -> str:
        return ':D'

    assert d.convert_list_to_kwargs(func0, []) == {}


def test_convert_list_arg():

    def some_func(s_list: t.List[str]) -> str:
        return ','.join(s_list)

    assert d.convert_value(some_func, ['a', 'b', 'c']) == 'a,b,c'

    # This is surprising, until you remember strings are iterable.
    # Cracking down on this might forbid useful behaviors, so in it stays.
    assert d.convert_value(some_func, 'a') == 'a'

    assert d.convert_value(some_func, 'abc') == 'a,b,c'

    with pytest.raises(TypeError) as excinfo:
        d.convert_value(some_func, 42)
    assert 'sole argument to' in str(excinfo.value)
    assert 'cannot be satisified with value 42' in str(excinfo.value)

    with pytest.raises(TypeError) as excinfo:
        d.convert_value(some_func, [42])
    assert 'sole argument to' in str(excinfo.value)
    assert 'cannot be satisified with value [42]' in str(excinfo.value)


def test_convert_list_arg_to_type_when_possible():
    def some_func(g_list: t.List[Guid]) -> t.List[Guid]:
        return g_list

    expected_g_list = [Guid('a'), Guid('b'), Guid('c')]

    assert d.convert_value(some_func, expected_g_list) == expected_g_list

    a = d.convert_value(some_func, ['a', 'b', 'c'])
    assert a == expected_g_list


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
        actual = d.convert_value(
            Disc,
            [
                'I Could Never Forget That Sandwhich',
                'Someone Left a Bake Out Caked in Pain',
                'Tim Simpson Fireside Chat, 1978',
            ]
        )
        assert actual == self.expected_g_list[0]

    def test_convert_to_list_of_typed_list(self):
        actual = d.convert_value(
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


def test_convert_to_dict_of_dicts():
    mapping: TrackToArtistMapping = {
        Track('TA'): Artist('AA'),
        Track('TB'): Artist('AB')
    }

    assert d.convert_value(TrackToArtistMapping, mapping) == mapping

    assert d.convert_value(TrackToArtistMapping, {
            'TA': 'AA',
            'TB': 'AB',
        }) == mapping

    assert d.convert_value(t.Dict[Guid, TrackToArtistMapping], {
            'g': {
                'TA': 'AA',
                'TB': 'AB',
            }
        }) == {Guid('g'): mapping}


def test_convert_dictionary_to_kwargs():

    def func(a: int, b: str) -> str:
        return f'a={a}, b={b}'

    assert d.convert_dictionary_to_kwargs(func, {'a': 1, 'b': 'b'}) == {
        'a': 1, 'b': 'b'}

    def func2(a: int, b: str, c: bool=False) -> str:
        return f'a={a}, b={b}, c={c}'

    assert d.convert_dictionary_to_kwargs(
        func2, {'a': 1, 'b': 'a', 'c': True}) == {'a': 1, 'b': 'a', 'c': True}

    assert d.convert_dictionary_to_kwargs(func2, {'a': 1, 'b': 'a'}) == {
        'a': 1, 'b': 'a'}

    with pytest.raises(TypeError):
        d.convert_dictionary_to_kwargs(func2, {'a': 1})

    with pytest.raises(TypeError) as excinfo:
        d.convert_dictionary_to_kwargs(
            func2, {'a': 1, 'b': 'a', 'c': True, 'd': 4})

    assert 'the following parameters not accepted for' in str(excinfo.value)

    def func3(*args) -> str:
        return ' '.join(args)

    assert d.convert_dictionary_to_kwargs(func3, {}) == {}

    # TODO: Add a test with **kwargs here and in the list tests above!

    def func3_kwargs(**kwargs) -> dict:
        return kwargs

    assert d.convert_dictionary_to_kwargs(func3_kwargs, {'a': 1, 'b': 2}) == {
        'kwargs': {'a': 1, 'b': 2}}

    def func4_str_kwargs(**kwargs: str) -> dict:
        return kwargs

    assert d.convert_dictionary_to_kwargs(
        func4_str_kwargs, {}) == {}

    assert d.convert_dictionary_to_kwargs(
        func4_str_kwargs, {'magic': 'value'}) == {'kwargs': {'magic': 'value'}}

    with pytest.raises(TypeError) as excinfo:
        d.convert_dictionary_to_kwargs(
            func4_str_kwargs, {'magic': 1})

    assert 'problem converting argument "magic"' in str(excinfo.value)

    def func0() -> str:
        return ':D'

    assert d.convert_dictionary_to_kwargs(func0, {}) == {}


def test_convert_dict_to_class():
    assert d.convert_value(Guid, {'value': 'five'}).value == 'five'

    disc = d.convert_value(
        Disc,
        {
            'tracks': [
                {'name': '1'},
                '2',
            ],
        })

    assert len(disc.tracks) == 2
    assert disc.tracks[0].name == '1'
    assert disc.tracks[1].name == '2'


# TODO: add a test for t.Optional types as well as Unions in general
