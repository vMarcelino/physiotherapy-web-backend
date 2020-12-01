from backend.constants import CONSTANTS
import flask_restful
from typing import List
from http import HTTPStatus

from backend import helper_functions
import backend.database as db


class Logout(flask_restful.Resource):
    def post(self):
        cookie = f'Authorization=null; Max-Age=-1; HttpOnly; SameSite=Lax'
        if not CONSTANTS.debug:
            cookie += '; secure'
        return 'Logging out', HTTPStatus.OK, {'Set-Cookie': cookie}
