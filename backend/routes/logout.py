import flask_restful
from typing import List
from http import HTTPStatus

from backend import helper_functions
import backend.database as db


class Logout(flask_restful.Resource):
    def post(self):
        return 'Logging out', HTTPStatus.OK, {
            'Set-Cookie': f'Authorization=null; Max-Age=-1; Secure; HttpOnly; SameSite=Lax'
        }
