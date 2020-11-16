from backend.routes import TokenObject
from typing_extensions import Literal
from backend.jwt_classes.access_levels import AccessLevels
from typing import Optional, Sequence, Tuple, Union
import flask_restful
from http import HTTPStatus

from backend import helper_functions
from backend.constants import CONSTANTS
import backend.database as db


class PatientSignup(flask_restful.Resource):
    @helper_functions.args_from_json
    def post(self, email: str, name: str, password: str, cpf: str, remember_login: bool)->Union[ \
        Tuple[str, Literal[HTTPStatus.NOT_ACCEPTABLE]], # to accomodate the variable content string in the literal below
        Tuple[Literal[f'Password too short. Minimum {CONSTANTS.min_password_len} characters long'], Literal[HTTPStatus.NOT_ACCEPTABLE]],
        Tuple[Literal['Email already in use'], Literal[HTTPStatus.CONFLICT]],
        Tuple[TokenObject, Literal[HTTPStatus.CREATED], dict],
        ]:
        email = email.lower()

        existing_user: Optional[db.Authorization] = db.Authorization.query.filter_by(email=email).one_or_none()

        if existing_user is None:
            # existing_user_with_id = db.User.query.filter(db.User.personal_id == id).one_or_none()
            # if existing_user_with_id is not None:
            #     return 'ID already in use', HTTPStatus.CONFLICT

            if len(password) >= CONSTANTS.min_password_len:
                salt = helper_functions.generate_salt()
                hashed_password = helper_functions.hash_with_salt(password.encode('utf-8'), salt)
                new_user = db.Patient(name=name,
                                      cpf=cpf,
                                      authorization=db.Authorization(email=email, password=hashed_password, salt=salt))

                db.db.session.add(new_user)
                db.db.session.commit()

                patient_token = new_user.to_jwt(subject=new_user.authorization_id,
                                                access_level=AccessLevels.private)  # must be after commit to have id
                patient_auth_token = new_user.authorization.to_jwt(subject=new_user.authorization_id)

                cookie = f'Authorization={patient_auth_token}; HttpOnly; SameSite=Lax'
                if remember_login:
                    cookie += f"; Max-Age={CONSTANTS.auth_cookie_expiration}"
                if not CONSTANTS.debug:
                    cookie += '; secure'

                return_result: TokenObject = {'token': patient_token}
                return return_result, HTTPStatus.CREATED, {'Set-Cookie': cookie}

            else:
                return f'Password too short. Minimum {CONSTANTS.min_password_len} characters long', HTTPStatus.NOT_ACCEPTABLE

        else:
            return 'Email already in use', HTTPStatus.CONFLICT


class ProfessionalSignup(flask_restful.Resource):
    @helper_functions.args_from_json
    def post(self, email: str, name: str, password: str, cpf: str, registration_id: str, institution: str,
             remember_login: bool)->Union[ \
        Tuple[str, Literal[HTTPStatus.NOT_ACCEPTABLE]], # to accomodate the variable content string in the literal below
        Tuple[Literal[f'Password too short. Minimum {CONSTANTS.min_password_len} characters long'], Literal[HTTPStatus.NOT_ACCEPTABLE]],
        Tuple[Literal['Email already in use'], Literal[HTTPStatus.CONFLICT]],
        Tuple[TokenObject, Literal[HTTPStatus.CREATED], dict],
        ]:
        email = email.lower()

        existing_user: Optional[db.Authorization] = db.Authorization.query.filter_by(email=email).one_or_none()

        if existing_user is None:
            # existing_user_with_id = db.User.query.filter(db.User.personal_id == id).one_or_none()
            # if existing_user_with_id is not None:
            #     return 'ID already in use', HTTPStatus.CONFLICT

            if len(password) >= CONSTANTS.min_password_len:
                salt = helper_functions.generate_salt()
                hashed_password = helper_functions.hash_with_salt(password.encode('utf-8'), salt)
                new_user = db.Professional(name=name,
                                           cpf=cpf,
                                           registration_id=registration_id,
                                           institution=institution,
                                           authorization=db.Authorization(email=email,
                                                                          password=hashed_password,
                                                                          salt=salt))

                db.db.session.add(new_user)
                db.db.session.commit()

                professional_token = new_user.to_jwt(
                    subject=new_user.authorization_id,
                    access_level=AccessLevels.private)  # must be after commit to have id
                professional_auth_token = new_user.authorization.to_jwt(subject=new_user.authorization_id)

                cookie = f'Authorization={professional_auth_token}; HttpOnly; SameSite=Lax'
                if remember_login:
                    cookie += f"; Max-Age={CONSTANTS.auth_cookie_expiration}"
                if not CONSTANTS.debug:
                    cookie += '; secure'

                return_result: TokenObject = {'token': professional_token}
                return return_result, HTTPStatus.CREATED, {'Set-Cookie': cookie}

            else:
                return f'Password too short. Minimum {CONSTANTS.min_password_len} characters long', HTTPStatus.NOT_ACCEPTABLE

        else:
            return 'Email already in use', HTTPStatus.CONFLICT