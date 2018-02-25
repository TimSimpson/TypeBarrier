"""
Dynamically converts JSON-like arguments to the given types.

This also serves as the reference behavior for the other modules, which in
theory should be faster.
"""
import inspect
import typing as t


TwDict = t.Dict[str, t.Any]


def convert_dictionary_to_kwargs(target: t.Any, value: dict) -> t.Any:
    """Go from list to a kwargs dictionary."""
    sig = inspect.signature(target)
    result = {}
    var_keyword_param: t.Optional[inspect.Parameter] = None

    for p in sig.parameters.values():
        if p.kind == inspect.Parameter.VAR_KEYWORD:
            assert var_keyword_param is None
            var_keyword_param = p
        elif p.kind == inspect.Parameter.VAR_POSITIONAL:
            pass  # Can't do anything, just ignore
        else:
            if p.name not in value:
                if p.default == p.empty:
                    raise TypeError(f'missing a required argument: {p.name}')
                # Otherwise just let the default arg do its thang
            else:
                result[p.name] = convert_value(p.annotation, value[p.name])

    extra_dict_keys = set(value.keys()).difference(
        set(sig.parameters.keys()))
    if extra_dict_keys:
        if var_keyword_param:
            if var_keyword_param.annotation != inspect.Parameter.empty:
                for key in extra_dict_keys:
                    try:
                        result[key] = convert_value(
                            var_keyword_param.annotation, value[key])
                    except TypeError as te:
                        raise TypeError(f'problem converting argument "{key}" '
                                        'to annotated variable keyword arg '
                                        f'type {var_keyword_param.annotation} '
                                        f'found in {target}.')
            else:
                for key in extra_dict_keys:
                    result[key] = value[key]
        else:
            raise TypeError('the following parameters not accepted for '
                            f'"{target}" : {list(extra_dict_keys)}')
    return result


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
    else:
        if len(value) > len(result):
            raise TypeError(f'{target} takes {len(result)} positional '
                            f'argument(s) but {len(value)} were given')
    return result


T = t.TypeVar('T')


def convert_list(target: type, value: t.List) -> t.List[T]:
    if not issubclass(target, list):
        raise ValueError(f'"{target}" is not a subclass of list')
    element_type = t.Any
    type_args = getattr(target, '__args__', None)
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
    if not issubclass(target, dict):
        raise ValueError(f'"{target}" is not a subclass of dict')
    if not isinstance(value, dict):
        raise TypeError(f'can\'t convert "{value}" '
                        f'(type {type(value)}) to {target}')
    key_type, value_type = t.Any, t.Any
    type_args = getattr(target, '__args__', None)
    if type_args:
        if len(type_args) != 2:
            raise NotImplemented(f'do not know how to convert type "{target}"')
        key_type, value_type = type_args
    try:
        return {convert_value(key_type, k): convert_value(value_type, v)
                for k, v in value.items()}
    except TypeError as te:
        raise TypeError(f'can\'t convert "{value}" (type {type(value)}) '
                        f'to {target}.') from te


def convert_value(target: t.Any, value: t.Any) -> t.Any:
    """Given a callable target, apply value.

    target can be a typical type, in which case an instance of the class is
    returned, or a function or other callable, in which case `value` will
    be passed to the function somehow.

    In any case, lists and dictionaries and lists are passed as *args and
    **kwargs, except that for each item the types given by the annotations is
    checked and errors may be raised.
    """
    if target == t.Any:
        return value
    if inspect.isfunction(target):
        st = getattr(target, '__supertype__', None)
        if st:
            # This is probably a new type?
            return convert_value(st, value)
        # handle with the function calling code below:
    elif issubclass(target, dict):
        return convert_dictionary(target, value)
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

    # If the incoming value is a dictionary, we don't attempt to pass it in
    # as the single argument even if that's what the parameter list accepts.
    # Doing so would make things too confusing (what to do in the event of
    # variable keyword arguments?).
    if isinstance(value, dict):
        kwargs = convert_dictionary_to_kwargs(target, value)
        return target(**kwargs)

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
                arg = convert_value(param.annotation, value)
            except TypeError as te:
                raise TypeError(f'sole argument to {target} accepts type '
                                f'{param.annotation}; cannot be satisified '
                                f'with value {value}.') from te
            return target(arg)
    return target(value)
