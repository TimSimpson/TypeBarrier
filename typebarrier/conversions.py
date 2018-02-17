import inspect
import typing as t


TwDict = t.Dict[str, t.Any]


def convert_list_to_kwargs(target: t.Any, value: t.List) -> t.Any:
    """Go from list to a kwargs dictionary."""
    sig = inspect.signature(target)
    result = {}
    var_positional_param: t.Optional[t.Tuple[inspect.Parameter, int]] = None

    for index, p in enumerate(sig.parameters.values()):
        if p.kind == inspect.Parameter.VAR_KEYWORD:
            pass  # Can't do anything, just ignore
        elif p.kind == inspect.Parameter.VAR_POSITIONAL:
            assert var_positional_param is None
            var_positional_param = p, index
        else:
            if len(value) <= index:
                if p.default == inspect.Parameter.empty:
                    raise TypeError(f'missing a positional argument: {index}')
            else:
                result[p.name] = convert_value(p.annotation, value[index])

    if var_positional_param:
        param, index = var_positional_param

        if param.annotation != inspect.Parameter.empty:
            var_arg = []
            for index, element in enumerate(value[index:]):
                try:
                    var_arg.append(convert_value(param.annotation, element))
                except TypeError as te:
                    raise TypeError(f'problem converting element {index} in a '
                                    f'list of args for {target} variable '
                                    f'length args: {te}')
        else:
            var_arg = value[index:]
        result[param.name] = var_arg
    return result


T = t.TypeVar('T')


def convert_list(target: type, value: t.List) -> t.List[T]:
    print(f'pee={target}')
    if not issubclass(target, list):
        raise ValueError('"{target}" is not a subclass of list')
    type_args = getattr(target, '__args__', None)
    element_type = t.Any
    if type_args:
        if len(type_args) != 1:
            raise NotImplemented(f'do not know how to convert type "{target}"')
        element_type = type_args[0]
    try:
        return [convert_value(element_type, e) for e in value]
    except TypeError as te:
        raise TypeError(f'can\'t convert "{value}" (type {type(value)}) '
                        f'to {target}.') from te


def convert_dictionary(target: t.Any, value: t.Dict) -> t.Any:
    raise NotImplemented()


def convert_value(target: t.Any, value: t.Any) -> t.Any:
    """Given a callable target, apply value.

    target can be a typical type, in which case an instance of the class is
    returned, or a function or other callable, in which case `value` will
    be passed to the function somehow.

    In any case, lists and dictionaries and lists are passed as *args and
    **kwargs, except that for each item the types given by the annotations is
    checked and errors may be raised.
    """
    print(f'target={target}')
    if target == t.Any:
        return value
    if isinstance(value, dict):
        return convert_dictionary(target, value)
    elif inspect.isfunction(target):
        st = getattr(target, '__supertype__', None)
        if st:
            # This is probably a new type?
            return convert_value(st, value)
        # handle with the function calling code below:
    elif issubclass(target, list):
        return convert_list(target, value)
    elif issubclass(type(value), target):
        # The given type is a subtype of the type we need.
        return value

    # At this point, see if calling target and passing value as the first
    # argument will work.
    try:
        sig = inspect.signature(target)
    except ValueError:
        raise TypeError(f'can\'t convert "{value}" (type {type(value)}) '
                        f'to {target}.')

    params = [param
              for param in sig.parameters.values()
              if param.kind not in [inspect.Parameter.VAR_POSITIONAL,
                                    inspect.Parameter.VAR_KEYWORD]]
    if len(params) < 1:
        raise TypeError(f'{target} does not accept any parameters, cannot '
                        f'convert from value "{value}".')
    elif len(params) > 1:
        raise TypeError(f'{target} accepts {len(params)} parameters, '
                        f'cannot create from value "{value}".')
    param = params[0]
    if param.annotation:
        if param.annotation != target:
            try:
                convert_value(param.annotation, value)
            except TypeError as te:
                raise TypeError(f'sole argument to {target} accepts type '
                                f'{param.annotation}; cannot be satisified '
                                f'with value {value}.') from te
    # if param.annotation and not issubclass(param.annotation, params):  # type: ignore  # NOQA
    #     raise TypeError(f'sole argument to {target} accepts type '
    #                     f'{param.annotation}; cannot be satisified with '
    #                     f'value {value}.')
    return target(value)


def typeify_callable(target: t.Callable, d: TwDict) -> TwDict:
    return convert_dictionary(target, d)

    # result = {}
    # sig = inspect.signature(target)

    # var_keyword_param: t.Optional[inspect.Parameter] = None

    # for p in sig.parameters.values():
    #     print(p.name)
    #     print(p.kind)
    #     print(p.default)
    #     print(p.annotation)
    #     print(',')

    #     if p.kind == inspect.Parameter.VAR_KEYWORD:
    #         assert var_keyword_param is None
    #         var_keyword_param = p
    #     elif p.kind == inspect.Parameter.VAR_POSITIONAL:
    #         # This would work maybe for a list?
    #         raise TypeError('positional arguments not supported- can\'t '
    #                         f'convert parameter {p}')
    #     else:
    #         if p.name not in d:
    #             if p.default != p.empty:
    #                 raise TypeError(f'missing a required argument: {p.name}')
    #         else:
    #             result[p.name] = _convert(p.annotation, d[p.name])

    # extra_dict_keys = set(d.keys()).difference(
    #     set(sig.parameters.sig.parameter.keys()))
    # if var_keyword_param:
    #     result[var_keyword_param.name] = {
    #         name: d[name] for name in extra_dict_keys
    #     }

    # raise TypeError('How I do this?')

    # print('->')
    # print(sig.return_annotation)

    # print()

    # b = sig.bind(**d)
    # print(b)
    # return {}


def typeify(target: t.Any, d: TwDict) -> TwDict:
    """Given a """
    if callable(target):
        return typeify_callable(target, d)
    else:
        raise NotImplemented()
