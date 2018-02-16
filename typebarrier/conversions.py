import inspect
import typing as t


TwDict = t.Dict[str, t.Any]


def convert_list_args_to_kwargs(target: t.Any, value: t.List) -> t.Any:
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
                raise TypeError(f'missing a positional argument: {index}')
            result[p.name] = convert_value(p.annotation, value[index])

    if var_positional_param:
        param, index = var_positional_param
        result[param.name] = value[index:]


def convert_list(target: t.Any, value: t.List) -> t.Any:
    raise NotImplemented()


def convert_dictionary(target: t.Any, value: t.Dict) -> t.Any:
    raise NotImplemented()


def convert_value(target: t.Any, value: t.Any) -> t.Any:
    if isinstance(value, dict):
        return convert_dictionary(target, value)
    elif isinstance(value, list):
        return convert_list(target, value)
    elif inspect.isfunction(target):
        st = getattr(target, '__supertype__', None)
        if st:
            # This is probably a new type?
            return convert_value(st, value)
        # handle below:
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
        raise TypeError(f'{target} does accepts {len(params)} parameters, '
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
