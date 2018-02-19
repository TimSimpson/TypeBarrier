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

    def start_inline_func(self) -> str:
        """Call this before adding an inline func.

        The variable name used for the return value is returned here.
        """
        self._return_indent.append(self._indent)
        self._return_variables.append(self.make_var())
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


def convert_dictionary(code: CodeGen, target: t.Any, arg_var: str) -> None:
    """Writes code needed to convert a dictionary into the given type.

    "target" is known at generation time while arg_var is just a string
    representing the incoming argument value in the generated code.
    """
    code.add_line('raise NotImplemented()  # TODO: add dict code')


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
        raise NotImplemented()
        # return convert_dictionary(target, value)
    elif issubclass(target, list):
        raise NotImplemented()
        # return convert_list(target, value)

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
    convert_dictionary(code, target, arg_var)
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
