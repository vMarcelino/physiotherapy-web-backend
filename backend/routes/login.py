from typing_extensions import Literal, TypedDict
from backend.jwt_classes.access_levels import AccessLevels
from backend.constants import CONSTANTS
import flask_restful
from typing import List, Optional, Tuple, Union
from http import HTTPStatus

from backend import helper_functions
import backend.database as db


class LoginReturnType(TypedDict):
    token: str
    type: str


class Login(flask_restful.Resource):
    @helper_functions.args_from_json
    def post(self, email: str, password: str, remember_login: bool)->Union[ \
        Tuple[Literal['Wrong username or password'], Literal[HTTPStatus.UNAUTHORIZED]],
        Tuple[LoginReturnType, Literal[HTTPStatus.OK], dict]
        ]:
        email = email.lower()
        user: Optional[db.Authorization] = db.Authorization.query.filter_by(email=email).one_or_none()
        if user:
            hashed_password = helper_functions.hash_with_salt(password.encode(), user.salt)
            if hashed_password == user.password:
                user_auth_token = user.to_jwt(subject=user)
                user_token = user.owner.to_jwt(subject=user, access_level=AccessLevels.private)
                cookie = f'Authorization={user_auth_token}; HttpOnly; SameSite=Lax'
                if remember_login:
                    cookie += f"; Max-Age={CONSTANTS.auth_cookie_expiration}"
                if not CONSTANTS.debug:
                    cookie += '; secure'

                returned_data: LoginReturnType = {'token': user_token, 'type': type(user.owner).__name__}
                return returned_data, HTTPStatus.OK, {'Set-Cookie': cookie}
            else:
                msg = "passwords don't match:\n"
                msg += f"\tinput: {hashed_password} ({len(hashed_password)})\n"
                msg += f"\ttable: {user.password} ({len(user.password)})\n"
                msg += f"\t salt: {user.salt}"
                print(msg)
                # print(len(hashed_password), len(user.password))
        else:
            print('User not found')

        return 'Wrong username or password', HTTPStatus.UNAUTHORIZED
