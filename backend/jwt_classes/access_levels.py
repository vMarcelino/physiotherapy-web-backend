from enum import Enum
from typing import Generic, List, Type, Type, TypeVar, cast

T = TypeVar('T')
T2 = TypeVar('T2')


class AccessLevel(Generic[T]):
    level = -1
    __args__: List[Type]

    @classmethod
    def wrap(cls, t: T2) -> T2:
        return cls[t] # type: ignore

    def __repr__(self):
        return f'{type(self).__name__}({self.__args__[0]})'


class AccessLevels(Enum):
    min = 0
    id = 0
    public = 1
    personal = 2
    private = 3
    max = 99


class Id(AccessLevel[T]):
    '''Like Public level, but with less information'''
    level = AccessLevels.id.value


class Public(AccessLevel[T]):
    '''Information is available to anyone, enywhere'''
    level = AccessLevels.public.value


class Personal(AccessLevel[T]):
    '''Information is only available to the 
    owner and to those with special access'''
    level = AccessLevels.personal.value


class Private(AccessLevel[T]):
    '''Information is only available to the owner'''
    level = AccessLevels.private.value
