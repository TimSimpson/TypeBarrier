import inspect
import typing as t

from . import conversions as c  # NOQA


T = t.TypeVar('T')


class CodeGen:
    """Generates code for a function."""

    def __init__(self) -> None:
        self._vi = 0
        self._cv = 0
        self._lines: t.List[str] = []
        self._return_variables: t.List[str] = []
        self._namespace: t.Dict[str, t.Any] = {}
        self._indent = 0

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
        self._lines.append(' ' * self._indent + line)

    def add_lines(self, lines: t.List[str]) -> None:
        for line in lines:
            self.add_line(line)

    def add_return(self, expr: str) -> None:
        if self._return_variables:
            self._lines.append(f'{self._return_variables[-1]} = {expr}')
        else:
            self._lines.append(f'return {expr}')

    def start_inline_func(self) -> str:
        """Call this before adding an inline func.

        The variable name used for the return value is returned here.
        """
        self._return_variables.append(self.make_var())
        return self._return_variables[-1]

    def end_inline_func(self) -> None:
        """Call this after adding inline function code."""
        del self._return_variables[-1]

    def render(self) -> str:
        return '\n'.join(self._lines)


def convert_value(code: CodeGen, target: t.Any, arg_var: str) -> None:
    """Writes code needed to convert "arg_var" to arbitrary type "target".

    "target" is known at generation time while arg_var is just a string
    representing the argument value.
    """

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
        cv = code.inject_closure_var(target)
        code.add_line(f'if issubclass(type({arg_var}), {cv}):')
        code.indent()
        code.add_return(arg_var)
        code.dedent()

    # At this point, see if calling target and passing value as the first
    # argument will work.
    try:
        sig = inspect.signature(target)
    except ValueError:
        cv = code.inject_closure_var(target)
        code.add_line(
            f"""raise TypeError('can't convert "{{{arg_var}}}" """
            f"""(type {{type({arg_var})}}) to {{{cv}}}.')""")

    sig
    # # If the incoming value is a dictionary, we don't attempt to pass it in
    # # as the single argument even if that's what the parameter list accepts.
    # # Doing so would make things too confusing (what to do in the event of
    # # variable keyword arguments?).
    # if isinstance(value, dict):
    #     kwargs = convert_dictionary_to_kwargs(target, value)
    #     return target(**kwargs)

    # params = [param
    #           for param in sig.parameters.values()
    #           if param.kind not in [inspect.Parameter.VAR_POSITIONAL,
    #                                 inspect.Parameter.VAR_KEYWORD]]
    # if len(params) < 1:
    #     raise TypeError(f'{target} does not accept any parameters, cannot '
    #                     f'convert from value "{value}".')
    # elif len(params) > 1:
    #     raise TypeError(f'{target} accepts {len(params)} parameters, '
    #                     f'cannot create from value "{value}".')
    # param = params[0]
    # if param.annotation:
    #     if param.annotation != target:
    #         try:
    #             arg = convert_value(param.annotation, value)
    #         except TypeError as te:
    #             raise TypeError(f'sole argument to {target} accepts type '
    #                             f'{param.annotation}; cannot be satisified '
    #                             f'with value {value}.') from te
    #         return target(arg)
    # return target(value)
