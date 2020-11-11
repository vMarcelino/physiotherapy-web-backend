from backend.constants import CONSTANTS
import flask_restful
from typing import List
from http import HTTPStatus

from backend import helper_functions
import backend.database as db


class Login(flask_restful.Resource):
    @helper_functions.args_from_json
    def post(self, email: str, password: str, remember_login: bool):
        email = email.lower()
        user: db.User = db.User.query.filter_by(email=email).one_or_none()
        if user:
            hashed_password = helper_functions.hash_with_salt(password.encode(), user.salt)
            if hashed_password == user.password:
                encoded = user.to_jwt(auth=True, subject=user)
                cookie = f'Authorization={encoded}; HttpOnly; SameSite=Lax'
                if remember_login:
                    cookie += f"; Max-Age={CONSTANTS.auth_cookie_expiration}"
                return {'token': encoded}, HTTPStatus.OK, {'Set-Cookie': cookie}
            else:
                msg = "passwords don't match:\n"
                msg += f"\tinput: {hashed_password} ({len(hashed_password)})\n"
                msg += f"\ttable: {user.password} ({len(user.password)})\n"
                msg += f"\t salt: {user.salt}"
                print(msg)
                # print(len(hashed_password), len(user.password))
        else:
            print('User not found')

        return 'wrong username or password', HTTPStatus.UNAUTHORIZED
