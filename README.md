# Type Barrier

[![Build Status](https://travis-ci.org/TimSimpson/TypeBarrier.svg?branch=master)](https://travis-ci.org/TimSimpson/TypeBarrier)

[![Build status](https://ci.appveyor.com/api/projects/status/gyaabdspagf8ld8b/branch/master?svg=true)](https://ci.appveyor.com/project/TimSimpson/typebarrier/branch/master)



Allows type strong conversions from JSON-safe dictionaries to Python 3 type annotated code and back.

## Usage

!! Note: this package is still under construction, so what you see below is currently a lie.

Imagine you have a framework which may dispatch arbitrary arguments to a number of functions.

In Python, this is easy:


    d  = {'arg1': 1, 'arg2': '2'}

    class SomeValue:
        def __init__(self, name):
            self.name = name

    def some_func(arg1: int, arg2: SomeValue) -> str:
        number = arg1 + 10
        return f'{arg2.name}, {number}'

    some_func(**d)

However, there's no validation, so you'll get an AttributeError. All those beautiful Python 3 type annotations have gone to waste!

TypeBarrier helps situations like this by turning JSON compatible dictionaries like `d` into dictionaries containing all the Python types they need:

    import typebarrier

    d2 = typebarrier.typeify(some_func, d)
    assert isinstance(d2['arg2'], SomeValue)

TypeBarrier works by checking the annotations on Python 3 functions. This includes the `__init__` method of classes, meaning you can do fun things like this:

    import typing as t

    api_response = {
        'server': {
            'id': '<some-guid>',
            'name': 'Name',
            'volumes': [
                {
                    'size': 42,
                    'id': '<some-guid>',
                }
            ]
        }
    }

    Guid = t.NewType('Guid', str)

    class Volume:
        def __init__(self, id: Guid, size: int):
            self.id = id
            self.size = size

    class Server:
        def __init__(self, id: Guid, name: str, volumes: t.List[Volume]):
            self.id = id
            self.name = name
            self.volumes = volumes

    server = typebarrier.typeify(Server, api_response['server'])

    assert isinstance(server.volumes[0], Volume)
    assert server.volumes[0].size = 42

## Motivation

I'm creating TypeBarrier because nothing similar to it exists. Most frameworks that seem closest involve creating objects like this:

    class Server:
        id: Guid
        name: str
        volumes: t.List[Volume]

and using metaclasses or other magical tricks to create custom initializers and stuff. While this approach has its fans, it isn't actually compatible with MyPy and in some cases forfeits the ability to validate arguments to class initializers or forces you to write them out even when the framework just replaces them anyway, leading MyPy to validate using fakes that won't even be touched at runtime.

Additionally, TypeBarrier's approach allows it to be used with functions easier than existing serialization / validation libraries which only work with classes.

## Updates

### 0.0.1




