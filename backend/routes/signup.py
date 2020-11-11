from typing import Optional, Sequence
import flask_restful
from http import HTTPStatus

from backend import helper_functions
from backend.constants import CONSTANTS
import backend.database as db


class PatientSignup(flask_restful.Resource):
    @helper_functions.args_from_json
    def post(self, email: str, name: str, password: str, cpf: str, remember_login: bool):
        email = email.lower()

        existing_user: Optional[db.Patient] = db.Patient.query.filter_by(email=email).one_or_none()

        if existing_user is None:
            # existing_user_with_id = db.User.query.filter(db.User.personal_id == id).one_or_none()
            # if existing_user_with_id is not None:
            #     return 'ID already in use', HTTPStatus.CONFLICT

            if len(password) >= CONSTANTS.min_password_len:
                salt = helper_functions.generate_salt()
                hashed_password = helper_functions.hash_with_salt(password.encode('utf-8'), salt)
                new_user = db.Patient(password=hashed_password,
                                      email=email,
                                      salt=salt,
                                      name=name,
                                      cpf=cpf,
                                      authorization=db.Authorization())

                db.db.session.add(new_user)
                db.db.session.commit()

                patient_token = new_user.to_jwt(subject=new_user.authorization_id)  # must be after commit to have id
                patient_auth_token = new_user.authorization.to_jwt(subject=new_user.authorization_id)

                cookie = f'Authorization={patient_auth_token}; Secure; HttpOnly; SameSite=Lax'
                if remember_login:
                    cookie += f"; Max-Age={CONSTANTS.auth_cookie_expiration}"
                if not CONSTANTS.debug:
                    cookie +='; secure'

                return {'token': patient_token}, HTTPStatus.CREATED, {'Set-Cookie': cookie}

            else:
                return f'Password too short. Minimum {CONSTANTS.min_password_len} characters long', HTTPStatus.NOT_ACCEPTABLE

        else:
            return 'Email already in use', HTTPStatus.CONFLICT


class ProfessionalSignup(flask_restful.Resource):
    @helper_functions.args_from_json
    def post(self, email: str, name: str, password: str, cpf: str, registration_id: str, institution: str,
             remember_login: bool):
        email = email.lower()

        existing_user: Optional[db.Professional] = db.Professional.query.filter_by(email=email).one_or_none()

        if existing_user is None:
            # existing_user_with_id = db.User.query.filter(db.User.personal_id == id).one_or_none()
            # if existing_user_with_id is not None:
            #     return 'ID already in use', HTTPStatus.CONFLICT

            if len(password) >= CONSTANTS.min_password_len:
                salt = helper_functions.generate_salt()
                hashed_password = helper_functions.hash_with_salt(password.encode('utf-8'), salt)
                new_user = db.Patient(password=hashed_password,
                                      email=email,
                                      salt=salt,
                                      name=name,
                                      cpf=cpf,
                                      registration_id=registration_id,
                                      institution=institution,
                                      authorization=db.Authorization())

                db.db.session.add(new_user)
                db.db.session.commit()

                professional_token = new_user.to_jwt(
                    subject=new_user.authorization_id)  # must be after commit to have id
                professional_auth_token = new_user.authorization.to_jwt(subject=new_user.authorization_id)

                cookie = f'Authorization={professional_auth_token}; Secure; HttpOnly; SameSite=Lax'
                if remember_login:
                    cookie += f"; Max-Age={CONSTANTS.auth_cookie_expiration}"
                if not CONSTANTS.debug:
                    cookie +='; secure'

                return {'token': professional_token}, HTTPStatus.CREATED, {'Set-Cookie': cookie}

            else:
                return f'Password too short. Minimum {CONSTANTS.min_password_len} characters long', HTTPStatus.NOT_ACCEPTABLE

        else:
            return 'Email already in use', HTTPStatus.CONFLICT