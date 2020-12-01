from backend import database
from typing import Union
from backend.constants import CONSTANTS


def create_cookie(owner: Union[database.Patient, database.Professional], remember_login: bool):
    patient_auth_token = owner.authorization.to_jwt(subject=owner.authorization_id)
    cookie = f'Authorization={patient_auth_token}; HttpOnly; SameSite=Lax; Path=/api'
    if remember_login:
        cookie += f"; Max-Age={CONSTANTS.auth_cookie_expiration}"
    if not CONSTANTS.debug:
        cookie += '; secure'
    return cookie


def delete_cookie():
    cookie = f'Authorization=null; Max-Age=-1; HttpOnly; SameSite=Lax'
    if not CONSTANTS.debug:
        cookie += '; secure'
    return cookie