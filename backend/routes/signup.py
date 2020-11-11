from typing import Optional, Sequence
import flask_restful
from http import HTTPStatus

from backend import helper_functions
from backend.constants import CONSTANTS
import backend.database as db


class Signup(flask_restful.Resource):
    @helper_functions.args_from_json
    def post(self, email: str, name: str, password: str, remember_login: bool):
        email = email.lower()

        existing_user = db.User.query.filter_by(email=email).one_or_none()

        if existing_user is None:
            # existing_user_with_id = db.User.query.filter(db.User.personal_id == id).one_or_none()
            # if existing_user_with_id is not None:
            #     return 'ID already in use', HTTPStatus.CONFLICT

            if len(password) >= CONSTANTS.min_password_len:
                salt = helper_functions.generate_salt()
                hashed_password = helper_functions.hash_with_salt(password.encode('utf-8'), salt)
                new_user = db.User(password=hashed_password, email=email, salt=salt, name=name)


                db.db.session.add(new_user)
                db.db.session.commit()

                encoded = new_user.to_jwt(auth=True, subject=new_user)  # must be after commit to have id

                cookie = f'Authorization={encoded}; Secure; HttpOnly; SameSite=Lax'
                if remember_login:
                    cookie += f"; Max-Age={CONSTANTS.auth_cookie_expiration}"
                    
                return {'token': encoded}, HTTPStatus.CREATED, {'Set-Cookie': cookie}

            else:
                return f'Password too short. Minimum {CONSTANTS.min_password_len} characters long', HTTPStatus.NOT_ACCEPTABLE

        else:
            return 'Email already in use', HTTPStatus.CONFLICT