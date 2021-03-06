import ast
import textwrap
import typing as t

from . import codegen as cg
from . import dynamic as d  # NOQA

T = t.TypeVar('T')


def convert_dictionary_to_kwargs(target: type) -> t.Callable[[t.Any], dict]:
    code = cg.CodeGen()
    function_name = code.make_var()
    t_any_var_name = code.inject_closure_var(t.Any)
    target_var_name = code.inject_closure_var(target)
    code.add_line(f'def {function_name}(value: {t_any_var_name}) '
                  f'-> {target_var_name}:')
    code.indent()
    cg.convert_dictionary_to_kwargs(code, target, 'value')

    a = ast.parse(code.render())
    compiled_code = compile(a, filename='<generated code>', mode='exec')
    exec(compiled_code, code.namespace)
    return code.namespace[function_name]


def convert_list(target: type,
                 ) -> t.Callable[[t.List], t.List[T]]:
    if not issubclass(target, list):
        raise ValueError('"{target}" is not a subclass of list')
    element_type = t.Any
    type_args = getattr(target, '__args__', None)
    if type_args:
        if len(type_args) != 1:
            raise NotImplemented(f'do not know how to convert type "{target}"')
        element_type = type_args[0]  # NOQA

    # exec(textwrap.dedent("""
    #     print('hi')
    #     et = element_type
    #     print('hi2')
    #     def converter(value: t.List) -> t.List[T]:
    #         try:
    #             return [c.convert_value(et, e) for e in value]
    #         except TypeError as te:
    #             raise TypeError(
    #                 f'can\\'t convert "{value}" (type {type(value)}) '
    #                 f'to {target}.') from te
    #         """),
    #      globals(),
    #      locals())
    # f = locals()['converter']
    # f.et = element_type

    namespace = {
        'element_type': element_type,
        't': t,
        'd_conv': d.convert_value,
        'T': T,
    }
    a = ast.parse(textwrap.dedent("""
        def converter(value: t.List) -> t.List[T]:
            try:
                return [d_conv(element_type, e) for e in value]
            except TypeError as te:
                raise TypeError(
                    f'can\\'t convert "{value}" (type {type(value)}) '
                    f'to {target}.') from te
            """))
    code = compile(a, filename=__file__, mode='exec')
    exec(code, namespace)
    f = namespace['converter']
    return f


def convert_value(target: type) -> t.Callable[[t.Any], t.Any]:
    code = cg.CodeGen()
    function_name = code.make_var()
    t_any_var_name = code.inject_closure_var(t.Any)
    target_var_name = code.inject_closure_var(target)
    code.add_line(f'def {function_name}(value: {t_any_var_name}) '
                  f'-> {target_var_name}:')
    code.indent()
    cg.convert_value(code, target, 'value')

    a = ast.parse(code.render())
    compiled_code = compile(a, filename='<generated code>', mode='exec')
    exec(compiled_code, code.namespace)
    return code.namespace[function_name]
