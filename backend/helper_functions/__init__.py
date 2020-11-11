import datetime
import hashlib
from http import HTTPStatus
import inspect
import secrets
import string
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    Iterator,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

import flask
from travel_backpack.variables import ensure_type

from backend import jwt_classes
from backend.jwt_classes import is_type

from backend.helper_functions.time import *

try:
    from typing import Literal  # type: ignore
except:
    from typing_extensions import Literal

T = TypeVar('T')


def generate_cryptographically_random_string(size: int = 8) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(size))


def generate_salt(size: int = 128):
    return secrets.token_bytes(size)


def get_missing_fields(json: Dict[str, Any], fields: Sequence[str]) -> Set[str]:
    ensure_type(json, dict)
    missing_fields: Set[str] = set()
    if json:
        for field in fields:
            if field not in json:
                missing_fields.add(field)
    else:
        missing_fields = set(fields)

    return missing_fields


def are_fields_missing(json: Dict[str, Any],
                       *fields: str) -> Union[Tuple[Literal[True], str], Tuple[Literal[False], None]]:
    missing_fields = get_missing_fields(json, fields)
    if missing_fields:
        msg = 'Missing fields: ' + ', '.join(missing_fields)
        print(msg)
        return True, msg

    return False, None


def check_missing_fields(json: Dict[str, Any], *fields: str):
    any_fields_missing, missing_fields_message = are_fields_missing(json, *fields)
    if any_fields_missing:
        flask.abort(
            HTTPStatus.BAD_REQUEST,
            description=missing_fields_message,
        )


def convert_jwt_types(variables: Dict[str, Any], types: Dict[str, Type], subject: Union[str, int, None]):
    wrong_types: Dict[str, str] = {}

    class ConversionError(Exception):
        ...

    def _convert_type(var, variable_type) -> Tuple[bool, Any]:
        if jwt_classes.is_subclass(variable_type, jwt_classes.JwtObject):
            try:
                return jwt_classes.is_type(var, variable_type, subject=subject)

            except jwt_classes.JwtObjectDecodeError as ex:
                print(ex)
                print('invalid jwt object')
                raise ConversionError('invalild token->Invalid jwt object')

            except jwt_classes.JwtObjectCreationError as ex:
                print(ex)
                print('Probably old jwt object structure')
                raise ConversionError('invalid token->Probably old jwt object structure')

            except jwt.DecodeError:
                print('invalid jwt')
                raise ConversionError('invalild token->Invalid jwt')

        elif hasattr(variable_type, '__origin__') and variable_type.__origin__ == Union:
            for arg in variable_type.__args__:
                try:
                    correct_type, corrected_value = _convert_type(var, arg)
                except ConversionError as err:
                    continue

                if not correct_type:
                    continue
                else:
                    return correct_type, corrected_value
            raise ConversionError(
                f'invalid type->Expected {" or ".join(variable_type.__args__)} but got {type(variables[name])}')
        else:
            return True, var

    for name, variable_type in types.items():
        if name in variables:
            try:
                correct_type, corrected_value = _convert_type(variables[name], variable_type)
            except ConversionError as err:
                wrong_types[name] = str(err)
                continue

            if not correct_type:
                wrong_types[name] = f'invalid type->Expected {variable_type} but got {type(variables[name])}'
            else:
                variables[name] = corrected_value

    if wrong_types:
        msg = 'The following variables are wrong: ' + ', '.join([f'{n}: {exp}' for n, exp in wrong_types.items()])
        flask.abort(HTTPStatus.BAD_REQUEST, description=msg)


def check_types(json: Dict[str, Any], types: Dict[str, Type]):
    wrong_types: Dict[str, Tuple[Type, Type]] = {}

    for name, variable_type in types.items():
        if jwt_classes.is_subclass(variable_type, jwt_classes.JwtObject):
            variable_type = cast(jwt_classes.JwtObject, variable_type.__origin__)  # type: ignore

        elif hasattr(variable_type, '__origin__'):
            if variable_type.__origin__ == Union:  # type: ignore
                variable_type = cast(Tuple[Type, ...], variable_type.__args__)  # type: ignore
                for i, var in enumerate(variable_type):
                    if jwt_classes.is_subclass(var, jwt_classes.JwtObject):
                        variable_type = list(variable_type)
                        variable_type[i] = var.__origin__  # type: ignore
                variable_type = tuple(variable_type)
            else:
                raise NotImplementedError(
                    f'variable type has __origin__ but is not union. var: {variable_type}, origin: {variable_type.__origin__}'  # type: ignore
                )

        if variable_type != inspect.Parameter.empty and name in json:
            try:
                ensure_type(json[name], variable_type, Any)
            except TypeError:
                wrong_types[name] = (variable_type, type(json[name]))

    if wrong_types:
        msg = 'The following variable types are wrong: ' + ', '.join(
            [f'{n} expected {exp} but got {variable_type}' for n, (exp, variable_type) in wrong_types.items()])
        flask.abort(HTTPStatus.BAD_REQUEST, description=msg)


def hash_with_salt(payload: bytes, salt: bytes):
    return hashlib.sha512(payload + salt).digest()


def to_dict(**kwargs):
    return kwargs


def check_user_auth_token(token: str):
    try:
        return jwt_classes.Authorization.from_jwt(token, subject=None)

    except jwt_classes.JwtObjectDecodeError as ex:
        print(ex)
        print('invalid jwt object')
        flask.abort(
            HTTPStatus.UNAUTHORIZED,
            description="Invalid Token object",
        )
    except jwt_classes.JwtObjectCreationError as ex:
        print(ex)
        print('Probably old jwt object structure')
        flask.abort(
            HTTPStatus.UNAUTHORIZED,
            description="Invalid Token. Please request a new one",
        )

    except jwt.DecodeError:
        print('invalid jwt')
        flask.abort(
            HTTPStatus.UNAUTHORIZED,
            description="Invalid Token",
        )


def first_or_abort(generator: Iterator[T], error_message: str, error_code: int = HTTPStatus.NOT_FOUND) -> T:
    try:
        return next(generator)

    except StopIteration:
        flask.abort(status=error_code, description=error_message)


F = TypeVar('F', bound=Callable[..., Any])


def str_money_to_int_cents(value: str) -> int:
    str_split_value = value.split('.')
    int_value = int(str_split_value[0]) * 100
    if len(str_split_value) == 2:
        int_value += int(str_split_value[1])

    return int_value


def int_cents_to_str_money(value: int) -> str:
    str_value = str(value).rjust(3, '0')
    return str_value[:-2] + '.' + str_value[-2:]


class copy_signature(Generic[F]):
    def __init__(self, target: F) -> None:
        ...

    def __call__(self, wrapped: Callable[..., Any]) -> F:
        ...


from backend.helper_functions.decorators import *