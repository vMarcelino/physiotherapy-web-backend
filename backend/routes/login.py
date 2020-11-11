from backend.jwt_classes.access_levels import AccessLevels
from backend.constants import CONSTANTS
import flask_restful
from typing import List, Optional
from http import HTTPStatus

from backend import helper_functions
import backend.database as db


class PatientLogin(flask_restful.Resource):
    @helper_functions.args_from_json
    def post(self, email: str, password: str, remember_login: bool):
        email = email.lower()
        user: Optional[db.Patient] = db.Patient.query.filter_by(email=email).one_or_none()
        if user:
            hashed_password = helper_functions.hash_with_salt(password.encode(), user.salt)
            if hashed_password == user.password:
                patient_auth_token = user.authorization.to_jwt(subject=user.authorization)
                patient_token = user.to_jwt(subject=user.authorization)
                cookie = f'Authorization={patient_auth_token}; HttpOnly; SameSite=Lax'
                if remember_login:
                    cookie += f"; Max-Age={CONSTANTS.auth_cookie_expiration}"
                if not CONSTANTS.debug:
                    cookie += '; secure'
                return {'token': patient_token}, HTTPStatus.OK, {'Set-Cookie': cookie}
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


class ProfessionalLogin(flask_restful.Resource):
    @helper_functions.args_from_json
    def post(self, email: str, password: str, remember_login: bool):
        email = email.lower()
        user: Optional[db.Professional] = db.Professional.query.filter_by(email=email).one_or_none()
        if user:
            hashed_password = helper_functions.hash_with_salt(password.encode(), user.salt)
            if hashed_password == user.password:
                professional_auth_token = user.authorization.to_jwt(subject=user.authorization)
                professional_token = user.to_jwt(subject=user.authorization, access_level=AccessLevels.private)
                cookie = f'Authorization={professional_auth_token}; HttpOnly; SameSite=Lax'
                if remember_login:
                    cookie += f"; Max-Age={CONSTANTS.auth_cookie_expiration}"
                if not CONSTANTS.debug:
                    cookie += '; secure'
                return {'token': professional_token}, HTTPStatus.OK, {'Set-Cookie': cookie}
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
