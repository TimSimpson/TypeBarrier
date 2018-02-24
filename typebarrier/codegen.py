import inspect
import typing as t


T = t.TypeVar('T')


def esq(whatevs: t.Any) -> str:
    """escape single quotes"""
    return str(whatevs).replace("'", "\\'")


class CodeGen:
    """Generates code for a function."""

    def __init__(self) -> None:
        self._vi = 0
        self._cv = 0
        self._lines: t.List[str] = []
        self._return_variables: t.List[str] = []
        self._namespace: t.Dict[str, t.Any] = {}
        self._indent = 0
        self._return_indent: t.List[int] = []

    def dedent(self) -> None:
        self._indent -= 1

    def indent(self) -> None:
        self._indent += 1

    def inject_closure_var(self, var: t.Any) -> str:
        """Adds variable to `namespace` dictionary. Returns key"""
        for k, v in self._namespace.items():
            if v == var:
                return k

        self._cv += 1
        name = f'cv{self._cv}'
        self._namespace[name] = var
        return name

    def make_var(self) -> str:
        """Creates a new variable name (just a unique string)."""
        self._vi += 1
        return f'v{self._vi}'

    def add_line(self, line: str) -> None:
        self._lines.append(' ' * self._indent * 4 + line)

    def add_lines(self, lines: t.List[str]) -> None:
        for line in lines:
            self.add_line(line)

    def add_return(self, expr: str) -> None:
        if self._return_variables:
            self.add_line(f'{self._return_variables[-1]} = {expr}')
        else:
            self.add_line(f'return {expr}')

    def start_inline_func(self, return_var: t.Optional[str]=None) -> str:
        """Call this before adding an inline func.

        The variable name used for the return value is returned here.
        """
        self._return_indent.append(self._indent)
        self._return_variables.append(return_var or self.make_var())
        return self._return_variables[-1]

    def end_inline_func(self) -> None:
        """Call this after adding inline function code."""
        assert self._indent >= self._return_indent[-1]
        self._indent = self._return_indent.pop()
        del self._return_variables[-1]

    def render(self) -> str:
        return '\n'.join(self._lines)

    @property
    def namespace(self) -> t.Dict[str, t.Any]:
        return self._namespace


def convert_dictionary_to_kwargs(code: CodeGen,
                                 target: t.Any,
                                 arg_var: str) -> None:
    """
    Produces code which, given a target, returns a dictionary of
    keyword arguments.
    """
    sig = inspect.signature(target)
    var_keyword_param: t.Optional[inspect.Parameter] = None

    check_key_error = False

    result_var = code.make_var()
    code.add_line(f'{result_var} = {{}}')

    for p in sig.parameters.values():
        if p.kind == inspect.Parameter.VAR_KEYWORD:
            assert var_keyword_param is None
            var_keyword_param = p
        elif p.kind == inspect.Parameter.VAR_POSITIONAL:
            pass  # Can't do anything, just ignore
        else:
            if p.default == p.empty:
                if not check_key_error:
                    check_key_error = True
                    code.add_line('try:')
                    code.indent()
            else:
                code.add_line(f'if \'{p.name}\' in {arg_var}:')
                code.indent()

            code.start_inline_func(f'{result_var}["{p.name}"]')
            # Add this arg to the eventual call
            convert_value(code,
                          p.annotation,
                          f'{arg_var}["{p.name}"]')
            code.end_inline_func()
            if p.default != p.empty:  # if this was in an if statement
                code.dedent()

    if check_key_error:
        # in except clause, resurface any key errors as a TypeError
        code.dedent()
        ke_var = code.make_var()
        code.add_line(f'except KeyError as {ke_var}:')
        code.indent()
        code.add_line("""raise TypeError(f'missing a required argument: """
                      f"""{{{ke_var}}}') from {ke_var}""")
        code.dedent()

    # OK, now that the conversion of normal params is done, have to deal
    # with kwazy kwargs
    possible_kwargs = code.make_var()
    code.add_line(f'{possible_kwargs} = set('
                  + ','.join(f"'{k}'" for k in sig.parameters.keys()) + ')')

    extra_dict_keys_var = code.make_var()
    code.add_line(f'{extra_dict_keys_var} = set({arg_var}.keys()).difference('
                  f'{possible_kwargs})')
    if var_keyword_param:
        if var_keyword_param.annotation != inspect.Parameter.empty:
            # Ugh, have to do type strong conversion just in case
            var_kwargs_var = code.make_var()
            code.add_line(f'{var_kwargs_var} = {{}}')
            key_var = code.make_var()
            code.add_line(f'for {key_var} in {extra_dict_keys_var}:')
            code.indent()  # START FOR LOOP
            code.add_line('try:')
            code.indent()  # START TRY
            code.start_inline_func(f'{var_kwargs_var}[{key_var}]')
            convert_value(code,
                          var_keyword_param.annotation,
                          f'{arg_var}[{key_var}]')
            code.end_inline_func()
            code.dedent()  # END TRY
            te_var = code.make_var()
            code.add_line(f'except TypeError as {te_var}:')
            code.indent()  # START EXCEPT
            code.add_line('raise TypeError(f\'problem converting argument '
                          f'"{{{key_var}}}" to annotated variable keyword '
                          f'are type {var_keyword_param.annotation} '
                          f'found in {target}.')
            code.dedent()  # END EXCEPT
            code.dedent()  # END FOR LOOP
            code.add_line(f'{result_var}[{var_keyword_param.name}] = '
                          f'{var_kwargs_var}')
        else:
            # simple conversion of extra stuff to the kwarg parameter
            code.add_line(f'{result_var}[{var_keyword_param.name}] = '
                          f'{{ name: {arg_var}[name] '
                          f'for name in {extra_dict_keys_var} }}')
    else:
        code.add_line(f'if {extra_dict_keys_var}:')
        code.indent()
        code.add_line("""raise TypeError(f'the following parameters not """
                      f"""accepted for "{target}" : """
                      f"""{{list({extra_dict_keys_var})}}')""")
    code.add_return(result_var)


def convert_list_to_kwargs(code: CodeGen,
                           target: t.Any,
                           arg_var: str) -> None:
    code.add_line('raise NotImplemented()')


# The goal of the method below is to be more efficient by not creating a
# dictionary if possible.
# def _convert_dictionary_value(code: CodeGen,
#                               target: t.Any,
#                               arg_var: str) -> None:
#     sig = inspect.signature(target)
#     var_keyword_param: t.Optional[inspect.Parameter] = None

#     check_key_error = False

#     possible_calls: t.List[t.List[str]] = []

#     call_index = code.make_var()
#     code.add_line(f'{call_index} = 0')

#     for p in sig.parameters.values():
#         if p.kind == inspect.Parameter.VAR_KEYWORD:
#             assert var_keyword_param is None
#             var_keyword_param = p
#         elif p.kind == inspect.Parameter.VAR_POSITIONAL:
#             pass  # Can't do anything, just ignore
#         else:
#             if p.default == p.empty:
#                 if not check_key_error:
#                     check_key_error = True
#                     code.add_line('try:')
#                     code.indent()
#             else:
#                 code.add_line(f'if \'{p.name}\' not in {arg_var}:')
#                 code.indent()
#                 code.add_line(f'{call_index} = {len(possible_calls)}')
#                 next_call = list(possible_calls[-1])  # make a copy
#                 possible_calls.append(next_call)
#                 code.dedent()
#                 code.add_line('else:')
#                 code.indent()

#             tmp_var = code.start_inline_func()
#             # Add this arg to the eventual call
#             possible_calls[-1].append(tmp_var)
#             convert_value(code,
#                           p.annotation,
#                           f'{arg_var}[\'{p.name}\']')
#             current_call.append(tmp_var)
#             code.end_inline_func()
#             if p.default != p.empty:
#                 code.dedent()

#     if check_key_error:
#         # in except clause, resurface any key errors as a TypeError
#         code.dedent()
#         ke_var = code.make_var()
#         code.add_line(f'except KeyError as {ke_var}:')
#         code.indent()
#         code.add_line("""raise TypeError(f'missing a required argument: """
#                       f"""{{{ke_var}}}') from {ke_var}""")
#         code.dedent()

#     # OK, now that the conversion of normal params is done, have to deal
#     # with kwazy kwargs
#     possible_kwargs = code.make_var()
#     code.add_line(f'{possible_kwargs} = set('
#         + ','.join(f"'{k}'" for k in sig.parameters.keys()) + ')')

#     extra_dict_keys_var = code.make_var()
#     code.add_line(f'{extra_dict_keys_var} = set({arg_var}.keys()).
#                                                   difference('
#                   f'{possible_kwargs})')
#     if not var_keyword_param:
#         code.add_line(f'if {extra_dict_keys_var}:')
#         code.indent()
#         code.add_line("""raise TypeError('the following parameters not """
#                       f"""accepted for "{target}" : """
#                       f"""{{list({extra_dict_keys_var})}}')""")
#     else:
#         if var_keyword_param.annotation != inspect.Parameter.empty:
#             # Ugh, have to do type strong conversion just in case
#         else:
#             # simple conversion of extra stuff to the kwarg parameter
#             code.add_line()

#             code.add_line(f'if "{p.name}" not in {arg_var}:')
#             code.indent()


def _convert_dictionary_to_target(code: CodeGen,
                                  target: t.Any,
                                  arg_var: str) -> None:
    # For now this is pretty simple
    # in the future it would be nice to make it more efficient in simple cases;
    kwargs_var = code.start_inline_func()
    convert_dictionary_to_kwargs(code, target, arg_var)
    code.end_inline_func()
    target_var_name = code.inject_closure_var(target)
    code.add_return(f'{target_var_name}(**{kwargs_var})')


def convert_list(code: CodeGen, target: t.Any, arg_var: str) -> None:
    if not issubclass(target, list):
        raise ValueError(f'"{target}" is not a subclass of list')
    element_type = t.Any
    type_args = getattr(target, '__args__', None)
    if type_args:
        if len(type_args) != 1:
            raise NotImplemented(f'do not know how to convert type "{target}"')
        element_type = type_args[0]

    code.add_line('try:')
    code.indent()  # START TRY    - this part is just a list comprehension in
    result_var = code.make_var()  # dynamic.py lol
    code.add_line(f'{result_var} = []')
    element_var = code.make_var()
    code.add_line(f'for {element_var} in {arg_var}:')
    code.indent()  # START FOR
    converted_element_var = code.start_inline_func()
    convert_value(code, element_type, element_var)
    code.end_inline_func()
    code.add_line(f'{result_var}.append({converted_element_var})')
    code.make_var()
    code.dedent()  # END FOR
    code.dedent()  # END TRY BODY
    te_var = code.make_var()
    code.add_line(f'except TypeError as {te_var}:')
    code.indent()
    code.add_line(f'raise TypeError(f\'can\\\'t convert "{{{arg_var}}} (type '
                  f'{{type({arg_var})}}" to {target}.\') from {te_var}')


def convert_dictionary(code: CodeGen, target: t.Any, arg_var: str) -> None:
    """Writes code needed to convert a dictionary into the given type.

    "target" is known at generation time while arg_var is just a string
    representing the incoming argument value in the generated code.
    """
    if not issubclass(target, dict):
        raise ValueError(f'"{target}" is not a subclass of dict')
    code.add_line(f'if not isinstance({arg_var}, dict):')
    code.indent()
    code.add_line(f'raise TypeError(f\'can\\\'t convert "{{{arg_var}}}" '
                  f'(type {{type({arg_var})}}) to {target}\')')
    code.dedent()

    key_type, value_type = t.Any, t.Any
    type_args = getattr(target, '__args__', None)
    if type_args:
        if len(type_args) != 2:
            raise NotImplemented(f'do not know how to convert type "{target}"')
        key_type, value_type = type_args

    code.add_line('try:')
    code.indent()  # BEGIN TRY BODY
    result_var = code.make_var()
    code.add_line(f'{result_var} = {{}}')
    k_var = code.make_var()
    v_var = code.make_var()
    code.add_line(f'for {k_var}, {v_var} in {arg_var}.items():')
    code.indent()  # BEGIN LOOP BODY

    new_k_var = code.start_inline_func()
    convert_value(code, key_type, k_var)
    code.end_inline_func()

    new_v_var = code.start_inline_func()
    convert_value(code, value_type, v_var)
    code.end_inline_func()

    code.add_line(f'{result_var}[{new_k_var}] = {new_v_var})')
    code.dedent()  # END FOR LOOP BODY
    code.add_return(result_var)
    code.dedent()  # END TRY BODY

    te_var = code.make_var()
    code.add_line(f'except TypeError as {te_var}:')
    code.indent()
    code.add_line(f'raise TypeError(f\'can\\\'t convert "{{{arg_var}}}" '
                  f'{{type({arg_var})}}) to {target}.\') from {te_var}')
    code.dedent()


def convert_value(code: CodeGen, target: t.Any, arg_var: str) -> None:
    """Writes code needed to convert "arg_var" to arbitrary type "target".

    "target" is known at generation time while arg_var is just a string
    representing the argument value.
    """
    target_var_name = code.inject_closure_var(target)
    print(f'target={target}')
    if target == t.Any:
        code.add_return(arg_var)
        return
    if inspect.isfunction(target):
        st = getattr(target, '__supertype__', None)
        if st:
            # This is probably a new type?
            return convert_value(code, st, arg_var)
        # handle with the function calling code below:
    elif issubclass(target, dict):
        return convert_dictionary(code, target, arg_var)
    elif issubclass(target, list):
        return convert_list(code, target, arg_var)

    if not inspect.isfunction(target):
        code.add_line(f'if issubclass(type({arg_var}), {target_var_name}):')
        code.indent()
        code.add_return(arg_var)
        code.dedent()
        code.add_line('else:')
        code.indent()

    # At this point, see if calling target and passing value as the first
    # argument will work.
    try:
        sig = inspect.signature(target)
    except ValueError:
        code.add_line(
            f"""raise TypeError(f'can\\'t convert "{{{arg_var}}}" """
            f"""(type {{type({arg_var})}}) to {{{target_var_name}}}.')""")
        return

    # If the incoming value is a dictionary, we don't attempt to pass it in
    # as the single argument even if that's what the parameter list accepts.
    # Doing so would make things too confusing (what to do in the event of
    # variable keyword arguments?).
    code.add_line(f'if isinstance({arg_var}, dict):')
    code.indent()
    _convert_dictionary_to_target(code, target, arg_var)
    code.dedent()
    code.add_line('else:')
    code.indent()

    params = [param
              for param in sig.parameters.values()
              if param.kind not in [inspect.Parameter.VAR_POSITIONAL,
                                    inspect.Parameter.VAR_KEYWORD]]
    if len(params) < 1:
        code.add_line(f"""raise TypeError(f'{esq(target)} does not accept """
                      """any parameters, cannot convert from value """
                      f"""{{{arg_var}}}.')""")
        return
    elif len(params) > 1:
        code.add_line(f"""raise TypeError(f'{esq(target)} accepts """
                      f"""{len(params)} parameters, cannot create from value"""
                      f""" "{{{arg_var}}}".')""")
        return
    param = params[0]
    if param.annotation:
        if param.annotation != target:  # avoid infinitie recursion
            code.add_line('try:')
            code.indent()
            return_value = code.start_inline_func()
            convert_value(code, param.annotation, arg_var)
            code.end_inline_func()
            code.dedent()
            var_name = code.make_var()
            code.add_line(f'except TypeError as {var_name}:')
            code.indent()
            code.add_line(f"""raise TypeError(f'sole argument to {esq(target)} accepts type {esq(param.annotation)}; cannot be satisified with value {{{arg_var}}}.') from {var_name}""")  # NOQA
            code.dedent()
            code.add_line(f'return {target_var_name}({return_value})')
