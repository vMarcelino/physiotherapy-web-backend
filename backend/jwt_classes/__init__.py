import datetime
from typing import (
    Any,
    Dict,
    Generic,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

import jwt

from backend.jwt_classes.access_levels import AccessLevel, AccessLevels
from backend.constants import CONSTANTS


class JwtObjectDecodeError(Exception):
    pass


class JwtObjectCreationError(Exception):
    pass


class JwtObjectAccessLevelError(JwtObjectDecodeError):
    pass


TJwt = TypeVar('TJwt', bound='JwtObject')

jwt_type_map: Dict[int, Type['JwtObject']] = {}


class JwtObjectMeta(type):
    def __new__(cls, name, bases, dct):
        c: Type[JwtObject] = cast(Type['JwtObject'], super().__new__(cls, name, bases, dct))
        jwt_type_map[c.__type__] = c
        return c


AL = TypeVar('AL')


class JwtObject(Generic[AL], metaclass=JwtObjectMeta):
    __type__ = 0
    __access_level__ = 0
    sub = None

    def __init__(self, subject: Union[str, int, None], access_level: AccessLevels = AccessLevels.max, **kwargs):
        if not hasattr(self, '__annotations__'):
            self.__annotations__ = {}
        self.__access_level__ = access_level.value
        self.sub = subject

        all_fields = set(self.__annotations__)
        required_fields = set(self.annotations)

        given_fields = set(kwargs)
        missing_fields = required_fields - given_fields
        extra_fields = given_fields - all_fields
        error_msgs = []
        if missing_fields:
            error_msgs.append(f'Missing fields: {list(missing_fields)}')
        if extra_fields:
            error_msgs.append(f'Extra fields: {list(extra_fields)}')
        if error_msgs:
            raise JwtObjectCreationError(f'Error instantiating token of type {self.__type__}. ' +
                                         ' & '.join(error_msgs))

        for variable_name, variable_type in self.annotations.items():
            value = kwargs.pop(variable_name)
            correct_type, value = is_type(value, variable_type, subject=self.sub)
            if correct_type:
                setattr(self, variable_name, value)
            else:
                raise ValueError(f'{variable_name} is not of type {variable_type}. is {type(value)}')

    @property
    def annotations(self) -> Dict[str, Type]:
        annotations: Dict[str, Type] = {}
        for field_name, field_type in self.__annotations__.items():
            if is_subclass(field_type, AccessLevel):
                if self.__access_level__ < field_type.level:
                    continue

            annotations[field_name] = field_type
        return annotations

    def to_dict(self, human_readable: bool = False):
        d = {variable_name: getattr(self, variable_name) for variable_name in self.annotations}

        def recurse(d):
            if isinstance(d, dict):
                for k, v in d.items():
                    if isinstance(v, JwtObject):
                        if human_readable:
                            d[k] = v.to_dict(human_readable=human_readable)
                        else:
                            d[k] = v.to_jwt()
                    elif isinstance(v, (list, dict)):
                        recurse(v)

            elif isinstance(d, list):
                for i in range(len(d)):
                    item = d[i]
                    if isinstance(item, JwtObject):
                        if human_readable:
                            d[i] = item.to_dict(human_readable=human_readable)
                        else:
                            d[i] = item.to_jwt()
                    elif isinstance(item, (list, dict)):
                        recurse(item)

        recurse(d)
        if human_readable:
            d['__type__'] = f'{jwt_type_map[self.__type__].__name__} ({self.__type__})'
            d['__access_level__'] = AccessLevels(self.__access_level__).name
        else:
            d['__type__'] = self.__type__
            d['__access_level__'] = self.__access_level__
        d['sub'] = self.sub
        return d

    def to_jwt(self):
        data = self.to_dict()
        data['iat'] = datetime.datetime.utcnow()
        data['iss'] = CONSTANTS.app_id
        # print('to_jwt:', data)
        return jwt.encode(payload=data, key=CONSTANTS.key, algorithm='HS256').decode()

    @staticmethod
    def from_any_jwt(jwt_str: str, subject: Union[str, int, None]) -> 'JwtObject':
        try:
            payload = jwt.decode(jwt=jwt_str, key=CONSTANTS.key, algorithms='HS256')
        except jwt.DecodeError:
            print('invalid jwt')
            raise
        # print('jwt payload:', payload)

        # check data type
        payload_data_type = payload.get('__type__', None)
        if payload_data_type == None:
            msg = f'Missing jwt type'
            print('invalid jwt object:', msg)
            raise JwtObjectDecodeError(msg)
        return jwt_type_map[payload_data_type].from_jwt(jwt_str, subject=subject)

    @classmethod
    def from_jwt(cls: Type[TJwt],
                 jwt_str: str,
                 subject: Union[str, int, None],
                 minimum_access_level: AccessLevels = AccessLevels.min) -> TJwt:
        try:
            payload = jwt.decode(jwt=jwt_str, key=CONSTANTS.key, algorithms='HS256')
        except jwt.DecodeError:
            print('invalid jwt')
            raise
        # print('jwt payload:', payload)

        # check data type
        payload_data_type = payload.get('__type__', None)
        if payload_data_type != cls.__type__:
            msg = f'Not the expected data type. expected {cls.__type__}, got {payload_data_type}'
            print('invalid jwt object:', msg)
            raise JwtObjectDecodeError(msg)

        # check access level
        payload_access_level = payload.get('__access_level__', None)
        if payload_access_level is None:
            msg = 'Missing access_level field'
            print('invalid jwt object:', msg)
            raise JwtObjectDecodeError(msg)
        if not isinstance(payload_access_level, int):
            msg = f'access_level field is not an int, is {type(payload_access_level)}'
            print('invalid jwt object:', msg)
            raise JwtObjectDecodeError(msg)
        if payload_access_level < minimum_access_level.value:
            msg = f'Access denied. Minimum access level: {minimum_access_level}, got {payload_access_level}'
            print('insufficient access for jwt object:', msg)
            raise JwtObjectAccessLevelError(msg)

        # check subject
        sub = payload.get('sub', None)  # subject (the one that can use the token)
        if subject is not None and sub != subject:
            msg = 'Subject is not valid'
            print('invalid jwt object:', msg)
            raise JwtObjectDecodeError(msg)

        payload.pop('sub')  # subject (the one that can use the token)
        payload.pop('iat')  # issued at
        payload.pop('iss')  # issuer (this app)
        # payload.pop('exp')  # expires at
        payload.pop('__type__')
        payload.pop('__access_level__')
        return cls(subject=sub, access_level=AccessLevels(payload_access_level), **payload)

    def downgrade_access(self, access_level: AccessLevels):
        for field_name, field_type in self.__annotations__.items():
            if is_subclass(field_type, AccessLevel):
                if access_level.value < field_type.level:
                    if hasattr(self, field_name):
                        delattr(self, field_name)
        self.__access_level__ = access_level.value

    def __eq__(self, other: Union[dict, 'JwtObject']):
        if isinstance(other, JwtObject):
            return self.to_dict() == other.to_dict()
        elif isinstance(other, dict):
            return self.to_dict() == other
        else:
            return False

    def __repr__(self):
        return f'{type(self).__name__}[{AccessLevels(self.__access_level__).name}]({str(self.to_dict(human_readable=True))})'


def is_subclass(variable_type: Type, expected_type: Union[Type, Tuple[Type, ...]]) -> bool:
    if hasattr(variable_type, '__origin__'):
        return is_subclass(variable_type.__origin__, expected_type)  # type: ignore
    else:
        try:
            return issubclass(variable_type, expected_type)
        except:
            return False


def is_type(value: Any, variable_type: Type, subject: Union[str, int, None]) -> Tuple[bool, Any]:
    if is_subclass(variable_type, AccessLevel):
        if len(variable_type.__args__) != 1:  # type: ignore
            raise NotImplementedError
        variable_type = variable_type.__args__[0]  # type: ignore

    if hasattr(variable_type, '__origin__') and not is_subclass(variable_type, JwtObject):
        if variable_type.__origin__ == Union:  # type: ignore
            variable_type = variable_type.__args__  # type: ignore
        elif variable_type.__origin__ == list:  # type: ignore
            args = variable_type.__args__  # type: ignore
            if len(args) == 1:
                if isinstance(value, list):
                    for i in range(len(value)):
                        correct_type, new_value = is_type(value[i], args[0], subject=subject)
                        if not correct_type:
                            return False, value
                        else:
                            value[i] = new_value
            else:
                raise NotImplementedError
            variable_type = list
        else:
            raise NotImplementedError

    elif is_subclass(variable_type, JwtObject):
        access_level: AccessLevel = variable_type.__args__[0]  # type: ignore
        access_level_e = AccessLevels(access_level.level)
        if isinstance(value, str):
            value = cast(JwtObject, variable_type).from_jwt(value, subject=subject, minimum_access_level=access_level_e)
        value.downgrade_access(access_level_e)
        variable_type = variable_type.__origin__  # type: ignore

    return isinstance(value, variable_type), value  # type: ignore


from .classes import *