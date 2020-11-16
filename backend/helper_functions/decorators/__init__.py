from backend.helper_functions.time import timestamp_to_datetime
from backend.constants import CONSTANTS
from backend.jwt_classes import JwtObject
from backend import database
import functools
from copy import deepcopy
from http import HTTPStatus
import inspect
from pprint import pformat
from typing import (
    Any,
    Callable,
    Dict,
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
import jwt

from backend import jwt_classes
from backend.helper_functions import check_missing_fields, check_types, check_user_auth_token, convert_jwt_types

try:
    from typing import Literal  # type: ignore
except:
    from typing_extensions import Literal


def check_parameters(source: Dict[str, Any], func, type_check: Callable[[Dict[str, Any], Dict[str, Type]], None],
                     subject: Union[str, int, None]):
    params = tuple(inspect.signature(func).parameters.values())[1:]  # remove first (self)
    param_types = {p.name: p.annotation for p in params}
    required_params = [p.name for p in params if p.default == p.empty]
    optional_params = {p.name: p.default for p in params if p.default != p.empty}
    check_missing_fields(source, *required_params)
    convert_jwt_types(source, param_types, subject=subject)
    if type_check:
        type_check(source, param_types)

    args = {p: source[p] for p in required_params}
    for k in optional_params:
        if k in source:
            args[k] = source[k]
        else:
            args[k] = optional_params[k]

    return args


def extract_doc(func, location: str):
    func_inspection = inspect.signature(func)
    params = tuple(func_inspection.parameters.values())[1:]  # remove first (self)
    param_types = {p.name: p.annotation for p in params}
    param_defaults = {p.name: p.default for p in params}
    required_params = [p.name for p in params if p.default == p.empty]
    optional_params = {p.name: p.default for p in params if p.default != p.empty}

    return_types = func_inspection.return_annotation
    response_codes = {}
    if hasattr(return_types, '__args__'):
        for return_type in return_types.__args__:
            if hasattr(return_type, '__origin__') and \
                issubclass(return_type.__origin__, Tuple) and \
                len(return_type.__args__) == 2 and \
                hasattr(return_type.__args__[1], '__origin__') and \
                return_type.__args__[1].__origin__ == Literal and \
                isinstance(return_type.__args__[1].__args__[0], int):

                return_annotation, return_code = return_type.__args__
                return_code = int(return_code.__args__[0])
                if hasattr(return_annotation, '__origin__') and return_annotation.__origin__ == Literal:
                    return_annotation = return_annotation.__args__[0]
                response_codes[return_code] = str(return_annotation)
            else:
                print(return_type)

    def to_OAS_type(t) -> str:
        if hasattr(t, '__origin__'):
            origin = t.__origin__
            if origin is Union:
                args = t.__args__
                if len(args) == 2 and args[1] is type(None):
                    return to_OAS_type(args[0])

            elif issubclass(origin, jwt_classes.JwtObject):
                return 'string'

        elif issubclass(t, bool):
            return 'boolean'

        elif issubclass(t, str):
            return 'string'

        elif issubclass(t, int):
            return 'integer'

        elif issubclass(t, float):
            return 'number'

        elif issubclass(t, dict):
            return 'object'

        elif issubclass(t, list):
            return 'array'

        raise NotImplementedError(t)

    if location == 'body':
        return {
            "parameters": [{
                "name": "parameters",
                "in": location,
                "schema": {
                    "type": "object",
                    "required": [param_name for param_name in required_params],
                    "properties": {p.name: {
                        "type": to_OAS_type(param_types[p.name])
                    }
                                   for p in params}
                },
                "required": True,
            }],
            "responses": {str(k): {
                "description": v
            }
                          for k, v in response_codes.items()}
        }
    else:
        return {
            "parameters": [
                *[{
                    "name": param_name,
                    "in": location,
                    "type": to_OAS_type(param_types[param_name]),
                    "required": True,
                } for param_name in required_params], *[{
                    "name": param_name,
                    "in": location,
                    "type": to_OAS_type(param_types[param_name]),
                    "required": False,
                    "default": param_defaults[param_name]
                } for param_name in optional_params]
            ],
            "responses": {str(k): {
                "description": v
            }
                          for k, v in response_codes.items()}
        }


_extracted_docs = {}


def args_from_json(func):
    """Checks and gets the function args from the json received

    Arguments:
        func {function} -- the function to be decorated
    """
    module = func.__module__
    func_class, func_name = func.__qualname__.split('.')
    if module not in _extracted_docs:
        _extracted_docs[module] = {}
    if func_class not in _extracted_docs[module]:
        _extracted_docs[module][func_class] = {}

    _extracted_docs[module][func_class][func_name] = extract_doc(func, location='body')

    def args_from_json_w(self):  # don't wrap
        json = {}
        json.update(flask.request.json)
        if CONSTANTS.debug:
            print('JSON received:')
            _pprint_items(json)

        token = flask.request.cookies.get('Authorization', None)
        subject = None
        if token is not None:
            subject = jwt_classes.Authorization.from_jwt(token, subject=None)._id
        args = check_parameters(source=json, func=func, type_check=check_types, subject=subject)
        return func(self, **args)

    return args_from_json_w


def args_from_urlencoded(func):
    """Checks and gets the function args from the json received

    Arguments:
        func {function} -- the function to be decorated
    """
    module = func.__module__
    func_class, func_name = func.__qualname__.split('.')
    if module not in _extracted_docs:
        _extracted_docs[module] = {}
    if func_class not in _extracted_docs[module]:
        _extracted_docs[module][func_class] = {}

    _extracted_docs[module][func_class][func_name] = extract_doc(func, location='query')

    def args_from_urlencoded_w(self):  # don't wrap
        query_args: Dict[str, str] = {}
        query_args.update(flask.request.args)
        if CONSTANTS.debug:
            print('Query args received:')
            _pprint_items(query_args)

        token = flask.request.cookies.get('Authorization', None)
        subject = None
        if token is not None:
            subject = jwt_classes.Authorization.from_jwt(token, subject=None)._id
        args = check_parameters(source=query_args, func=func, type_check=convert_types, subject=subject)
        return func(self, **args)

    convertible_types = set((int, float, bool))

    def convert_types(variables: Dict[str, Any], types: Dict[str, Type]):
        wrong_types: Set[str] = set()

        for name, variable_type in types.items():
            if variable_type != inspect.Parameter.empty and variable_type in convertible_types and name in variables:
                try:
                    variables[name] = variable_type(variables[name])
                except TypeError:
                    wrong_types.add(name)

        if wrong_types:
            msg = 'The following variable types are wrong: ' + ', '.join(
                [f'{n} expected {types[n]}' for n in wrong_types])
            flask.abort(HTTPStatus.BAD_REQUEST, description=msg)

    return args_from_urlencoded_w


def _pprint_items(obj: Dict[str, Any]):
    for key, value in obj.items():
        try:
            if key.endswith('_token'):
                try:
                    p_value = JwtObject.from_any_jwt(value, subject=None).to_dict(human_readable=True)
                except:
                    p_value = jwt.decode(value, verify=False)
            elif key.endswith('_date'):
                p_value = timestamp_to_datetime(int(value))
            else:
                p_value = value
        except Exception as ex:
            p_value = value
        print(pformat((key, p_value)))


def inject_user_from_authorization(func):
    signature = inspect.signature(func)
    param = tuple(signature.parameters.values())[1]
    param_type = param.annotation

    @functools.wraps(func)  # wrap to preserve original args
    def inject_user_from_authorization_w(self, *args, **kwargs):
        if 'Authorization' not in flask.request.cookies:
            flask.abort(
                HTTPStatus.UNAUTHORIZED,
                description="Missing Authorization cookie",
            )

        token = flask.request.cookies['Authorization']
        authorization = check_user_auth_token(token)

        if issubclass(param_type, int):
            return func(self, authorization._id, *args, **kwargs)
        elif issubclass(param_type, jwt_classes.Authorization):
            return func(self, authorization, *args, **kwargs)
        elif issubclass(param_type, database.Authorization):
            u = database.Authorization.get(authorization._id)
            if u is None:
                raise Exception('Authorization not found in database')
            return func(self, u, *args, **kwargs)
        else:
            raise NotImplementedError('The annotated type is not supported yet')

    return remove_parameter(inject_user_from_authorization_w)


def remove_parameter(func):
    '''
    Removes the first parameter after self from the signature
    '''
    @functools.wraps(func)  # wrap to preserve original args
    def remove_parameter_w(self, *args, **kwargs):
        return func(self, *args, **kwargs)

    original_signature = inspect.signature(func)
    params = tuple(original_signature.parameters.values())
    # remove first param (after self) from original signature
    new_params = params[0:1] + params[2:]
    new_signature = original_signature.replace(parameters=new_params)
    remove_parameter_w.__signature__ = new_signature  # sets the signature of the wrapper

    return remove_parameter_w


def session_remove(func):
    @functools.wraps(func)
    def session_remove_wrapper(*args, **kwargs):
        from backend import database as db  # because of circular imports
        result = func(*args, **kwargs)
        db.db.session.remove()
        return result

    @functools.wraps(session_remove_wrapper)
    def session_remove_wrapper_d(*args, **kwargs):
        print('\n')
        print('.')
        print('path:', flask.request.path)
        print('method:', flask.request.method)
        print('endpoint:', flask.request.endpoint)
        result = session_remove_wrapper(*args, **kwargs)
        if isinstance(result, tuple) and len(result) >= 1:
            new_result = deepcopy(result[0])
            if isinstance(new_result, dict):
                tok: Optional[str] = new_result.get('token', None)
                if tok:
                    new_result['token'] = JwtObject.from_any_jwt(tok, subject=None).to_dict(human_readable=True)
                print('result:', pformat((new_result, *result[1:]), indent=2))
            elif isinstance(new_result, list):
                for i, item in enumerate(new_result):
                    if isinstance(item, dict):
                        tok: Optional[str] = item.get('token', None)
                        if tok:
                            new_result[i]['token'] = JwtObject.from_any_jwt(tok,
                                                                            subject=None).to_dict(human_readable=True)
                print('result:', pformat((new_result, *result[1:]), indent=2))
            else:
                print('result:', result)
        else:
            print('result:', result)
        return result

    if CONSTANTS.debug:
        return session_remove_wrapper_d
    else:
        return session_remove_wrapper
