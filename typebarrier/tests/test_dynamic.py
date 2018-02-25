import os
import typing as t

import pytest

from typebarrier import dynamic
from typebarrier import inline


class DynamicCall:

    @staticmethod
    def convert_value(target: t.Type,
                      value: t.Any) -> t.Callable[[t.Any], None]:
        return dynamic.convert_value(target, value)

    @staticmethod
    def convert_dictionary_to_kwargs(target: t.Type,
                                     value: t.Any) -> dict:
        return dynamic.convert_dictionary_to_kwargs(target, value)


class InlineCall:

    @staticmethod
    def convert_value(target: t.Type,
                      value: t.Any) -> t.Callable[[t.Any], None]:
        return inline.convert_value(target)(value)

    @staticmethod
    def convert_dictionary_to_kwargs(target: t.Type,
                                     value: t.Any) -> dict:
        return inline.convert_dictionary_to_kwargs(target)(value)


def everything(func):
    return pytest.mark.parametrize('cnv', [DynamicCall, InlineCall])(func)


class DynamicProxyBM:

    def __init__(self, benchmark):
        self._benchmark = benchmark

    def convert_value(self, target: t.Type) -> t.Callable[[t.Any], t.Any]:
        def cb(value):
            result = dynamic.convert_value(target, value)
            self._benchmark(dynamic.convert_value, target, value)
            return result

        return cb

    def convert_dictionary_to_kwargs(self, target: t.Type) -> dict:
        def cb(value):
            result = dynamic.convert_dictionary_to_kwargs(target, value)
            self._benchmark(
                dynamic.convert_dictionary_to_kwargs, target, value)
            return result

        return cb


class InlineProxyBM:

    def __init__(self, benchmark):
        self._benchmark = benchmark

    def convert_value(self, target: t.Type) -> t.Callable[[t.Any], t.Any]:
        converter = inline.convert_value(target)

        def cb(value):
            result = converter(value)
            self._benchmark(converter, value)
            return result

        return cb

    def convert_dictionary_to_kwargs(self, target: t.Type) -> dict:
        converter = inline.convert_value(target)

        def cb(value):
            result = converter(value)
            self._benchmark(converter, value)
            return result

        return cb


class DynamicProxy:

    @staticmethod
    def convert_value(target: t.Type) -> t.Callable[[t.Any], t.Any]:
        return lambda value: dynamic.convert_value(target, value)

    @staticmethod
    def convert_dictionary_to_kwargs(target: t.Type) -> dict:
        return lambda value: dynamic.convert_dictionary_to_kwargs(
            target, value)


class InlineProxy:

    @staticmethod
    def convert_value(target: t.Type) -> t.Callable[[t.Any], t.Any]:
        return inline.convert_value(target)

    @staticmethod
    def convert_dictionary_to_kwargs(target: t.Type) -> dict:
        return inline.convert_dictionary_to_kwargs(target)


if os.environ.get('TYPIFY_BENCHMARK') == 'true':
    def do_both(func):
        @pytest.mark.parametrize('cnv', ['dynamic', 'inline'])
        def new_func(cnv, benchmark):
            if cnv == 'dynamic':
                c = DynamicProxyBM(benchmark)
            else:
                c = InlineProxyBM(benchmark)
            return func(c)

        return new_func
else:
    def do_both(func):
        @pytest.mark.parametrize('cnv', ['dynamic', 'inline'])
        def new_func(cnv):
            if cnv == 'dynamic':
                c = DynamicProxy()
            else:
                c = InlineProxy()
            return func(c)

        return new_func


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


@do_both
def test_primitives_str(cnv):
    # benchmark(dynamic.convert_value(int, 42))
    to_str = cnv.convert_value(str)
    assert to_str('some-string') == 'some-string'


@do_both
def test_primitives_int(cnv):
    to_int = cnv.convert_value(int)
    assert to_int(42) == 42


@do_both
def test_primitives_bool(cnv):
    to_bool = cnv.convert_value(bool)
    assert to_bool(True)


@everything
def test_primitives_raises(cnv):
    with pytest.raises(TypeError) as excinfo:
        cnv.convert_value(str, 42)
    assert ('can\'t convert "42" (type <class \'int\'>) '
            'to <class \'str\'>' in str(excinfo.value))


@do_both
def test_list_1(cnv):
    to_list = cnv.convert_value(list)
    assert to_list([1, 2, '3']) == [1, 2, '3']


@do_both
def test_list_2(cnv):
    to_list = cnv.convert_value(t.List[str])
    assert to_list(['a', 'b']) == ['a', 'b']


@do_both
def test_list_3(cnv):
    to_list = cnv.convert_value(list)
    assert to_list(range(5)) == [0, 1, 2, 3, 4]


@do_both
def test_list_4(cnv):
    to_list = cnv.convert_value(t.List[str])
    # def to_list(x):
    #     return dynamic.convert_value(t.List[str], x)

    assert (to_list((str(x) for x in range(5)))
            == ['0', '1', '2', '3', '4'])


@everything
def test_list_failures(cnv):
    with pytest.raises(TypeError) as excinfo:
        cnv.convert_value(list, 42)
    assert ('can\'t convert "42" (type <class \'int\'>) '
            'to <class \'list\'>' in str(excinfo.value))

    with pytest.raises(TypeError) as excinfo:
        cnv.convert_value(t.List[str], [1, 2, 3])
    assert ('can\'t convert "[1, 2, 3]" (type <class \'list\'>) '
            'to typing.List[str].' in str(excinfo.value))


@do_both
def test_dictionary(cnv):
    to_dict = cnv.convert_value(dict)
    assert to_dict({'a': 1, 2: 'b'}) == {'a': 1, 2: 'b'}


@do_both
def test_dictionary_type(cnv):
    to_dict = cnv.convert_value(t.Dict[str, int])
    assert to_dict({'a': 1, 'b': 2}) == {'a': 1, 'b': 2}


@everything
def test_dictionary_failures(cnv):
    with pytest.raises(TypeError) as excinfo:
        cnv.convert_value(dict, 42)
    assert ('can\'t convert "42" (type <class \'int\'>) '
            'to <class \'dict\'>' in str(excinfo.value))

    with pytest.raises(TypeError) as excinfo:
        cnv.convert_value(t.Dict[str, int], {1: 1})
    assert ('can\'t convert "{1: 1}" (type <class \'dict\'>) '
            'to typing.Dict[str, int].' in str(excinfo.value))

    with pytest.raises(TypeError) as excinfo:
        cnv.convert_value(t.Dict[str, int], {'a': 'b'})
    assert ('can\'t convert "{\'a\': \'b\'}" (type <class \'dict\'>) '
            'to typing.Dict[str, int].' in str(excinfo.value))


@do_both
def test_new_type(cnv):
    to_new_type = cnv.convert_value(NewTypeStr)
    assert to_new_type('some-string') == 'some-string'


@everything
def test_invalid_conversions(cnv):
    def some_func() -> int:
        return 42

    with pytest.raises(TypeError) as excinfo:
        cnv.convert_value(some_func, 42)

    assert 'does not accept any parameters,' in str(excinfo.value)


@do_both
def test_single_arg_func(cnv):

    def some_func(i: int) -> str:
        return f'index={i}'

    to_some_func = cnv.convert_value(some_func)
    assert to_some_func(78) == 'index=78'


@everything
def test_single_arg_func_from_wrong_type_fails(cnv):

    def some_func(i: int) -> str:
        return f'index={i}'

    with pytest.raises(TypeError) as excinfo:
        cnv.convert_value(some_func, 'hai')

    assert ('accepts type <class \'int\'>; cannot be satisified'
            in str(excinfo.value))


@do_both
def test_single_arg_class_init(cnv):
    to_guid = cnv.convert_value(Guid)
    guid = to_guid('happy')
    assert guid.value == 'happy'


@everything
def test_single_arg_class_init_from_wrong_type_fails(cnv):

    class Guid:
        def __init__(self, value: str) -> None:
            self.value = value

    with pytest.raises(TypeError) as excinfo:
        cnv.convert_value(Guid, 42)

    assert ('accepts type <class \'str\'>; cannot be satisified'
            in str(excinfo.value))


@everything
def test_two_arg_func(cnv):

    def some_func(a: int, b: int) -> str:
        return f'index={a}'

    with pytest.raises(TypeError) as excinfo:
        cnv.convert_value(some_func, 78)

    assert 'accepts 2 parameters, cannot create' in str(excinfo.value)


def test_convert_list_to_kwargs():
    cnv = dynamic

    def func(a: int, b: str) -> str:
        return f'a={a}, b={b}'

    assert cnv.convert_list_to_kwargs(func, [1, 'a']) == {'a': 1, 'b': 'a'}

    def func2(a: int, b: str, c: bool=False) -> str:
        return f'a={a}, b={b}, c={c}'

    assert cnv.convert_list_to_kwargs(func2, [1, 'a', True]) == {
        'a': 1, 'b': 'a', 'c': True}

    assert cnv.convert_list_to_kwargs(func2, [1, 'a']) == {
        'a': 1, 'b': 'a'}

    with pytest.raises(TypeError) as excinfo:
        cnv.convert_list_to_kwargs(func2, [1])

    with pytest.raises(TypeError) as excinfo:
        cnv.convert_list_to_kwargs(func2, [1, 'a', True, 4])

    assert '3 positional argument(s) but 4 were given' in str(excinfo.value)

    def func3(*args) -> str:
        return ' '.join(args)

    assert cnv.convert_list_to_kwargs(func3, []) == {'args': []}

    assert cnv.convert_list_to_kwargs(func3, [1, 2, 3]) == {'args': [1, 2, 3]}

    def func4(*args: str) -> str:
        return ' '.join(args)

    assert cnv.convert_list_to_kwargs(func4, []) == {'args': []}

    with pytest.raises(TypeError) as excinfo:
        cnv.convert_list_to_kwargs(func4, [1, 2, 3])

    assert ('problem converting element 0 in a list of args for '
            in str(excinfo.value))

    def func0() -> str:
        return ':D'

    assert cnv.convert_list_to_kwargs(func0, []) == {}


@do_both
def test_convert_list_arg_1(cnv):
    def some_func(s_list: t.List[str]) -> str:
        return ','.join(s_list)

    to_some_func = cnv.convert_value(some_func)
    assert to_some_func(['a', 'b', 'c']) == 'a,b,c'


@do_both
def test_convert_list_arg_2(cnv):
    def some_func(s_list: t.List[str]) -> str:
        return ','.join(s_list)

    # This is surprising, until you remember strings are iterable.
    # Cracking down on this might forbid useful behaviors, so in it stays.
    to_some_func = cnv.convert_value(some_func)
    assert to_some_func('a') == 'a'


@do_both
def test_convert_list_arg_3(cnv):
    def some_func(s_list: t.List[str]) -> str:
        return ','.join(s_list)

    to_some_func = cnv.convert_value(some_func)
    assert to_some_func('abc') == 'a,b,c'


@everything
def test_convert_list_arg_unhappy(cnv):
    def some_func(s_list: t.List[str]) -> str:
        return ','.join(s_list)

    with pytest.raises(TypeError) as excinfo:
        cnv.convert_value(some_func, 42)
    assert 'sole argument to' in str(excinfo.value)
    assert 'cannot be satisified with value 42' in str(excinfo.value)

    with pytest.raises(TypeError) as excinfo:
        cnv.convert_value(some_func, [42])
    assert 'sole argument to' in str(excinfo.value)
    assert 'cannot be satisified with value [42]' in str(excinfo.value)


@everything
def test_convert_list_arg_to_type_when_possible(cnv):
    def some_func(g_list: t.List[Guid]) -> t.List[Guid]:
        return g_list

    expected_g_list = [Guid('a'), Guid('b'), Guid('c')]

    assert cnv.convert_value(some_func, expected_g_list) == expected_g_list

    a = cnv.convert_value(some_func, ['a', 'b', 'c'])
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

    @everything
    def test_convert_to_typed_list(self, cnv):
        actual = cnv.convert_value(
            Disc,
            [
                'I Could Never Forget That Sandwhich',
                'Someone Left a Bake Out Caked in Pain',
                'Tim Simpson Fireside Chat, 1978',
            ]
        )
        assert actual == self.expected_g_list[0]

    @everything
    def test_convert_to_list_of_typed_list(self, cnv):
        actual = cnv.convert_value(
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


@everything
def test_convert_to_dict_of_dicts(cnv):
    mapping: TrackToArtistMapping = {
        Track('TA'): Artist('AA'),
        Track('TB'): Artist('AB')
    }

    assert cnv.convert_value(TrackToArtistMapping, mapping) == mapping

    assert cnv.convert_value(TrackToArtistMapping, {
            'TA': 'AA',
            'TB': 'AB',
        }) == mapping

    assert cnv.convert_value(t.Dict[Guid, TrackToArtistMapping], {
            'g': {
                'TA': 'AA',
                'TB': 'AB',
            }
        }) == {Guid('g'): mapping}


@everything
def test_convert_dictionary_to_kwargs(cnv):

    def func(a: int, b: str) -> str:
        return f'a={a}, b={b}'

    assert cnv.convert_dictionary_to_kwargs(func, {'a': 1, 'b': 'b'}) == {
        'a': 1, 'b': 'b'}

    def func2(a: int, b: str, c: bool=False) -> str:
        return f'a={a}, b={b}, c={c}'

    assert cnv.convert_dictionary_to_kwargs(
        func2, {'a': 1, 'b': 'a', 'c': True}) == {'a': 1, 'b': 'a', 'c': True}

    assert cnv.convert_dictionary_to_kwargs(func2, {'a': 1, 'b': 'a'}) == {
        'a': 1, 'b': 'a'}

    with pytest.raises(TypeError):
        cnv.convert_dictionary_to_kwargs(func2, {'a': 1})

    with pytest.raises(TypeError) as excinfo:
        cnv.convert_dictionary_to_kwargs(
            func2, {'a': 1, 'b': 'a', 'c': True, 'd': 4})

    assert 'the following parameters not accepted for' in str(excinfo.value)

    def func3(*args) -> str:
        return ' '.join(args)

    assert cnv.convert_dictionary_to_kwargs(func3, {}) == {}

    # TODO: Add a test with **kwargs here and in the list tests above!

    def func3_kwargs(**kwargs) -> dict:
        return kwargs

    assert cnv.convert_dictionary_to_kwargs(
        func3_kwargs,
        {'a': 1, 'b': 2}) == {'a': 1, 'b': 2}

    def func4_str_kwargs(**kwargs: str) -> dict:
        return kwargs

    assert cnv.convert_dictionary_to_kwargs(
        func4_str_kwargs, {}) == {}

    assert cnv.convert_dictionary_to_kwargs(
        func4_str_kwargs, {'magic': 'value'}) == {'magic': 'value'}

    with pytest.raises(TypeError) as excinfo:
        cnv.convert_dictionary_to_kwargs(
            func4_str_kwargs, {'magic': 1})

    assert 'problem converting argument "magic"' in str(excinfo.value)

    def func0() -> str:
        return ':D'

    assert cnv.convert_dictionary_to_kwargs(func0, {}) == {}


@everything
def test_convert_dict_to_class(cnv):
    assert cnv.convert_value(Guid, {'value': 'five'}).value == 'five'

    disc = cnv.convert_value(
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
