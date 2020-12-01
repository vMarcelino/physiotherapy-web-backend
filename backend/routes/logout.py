from backend import authorization
from backend.constants import CONSTANTS
import flask_restful
from typing import List
from http import HTTPStatus

from backend import helper_functions
import backend.database as db


class Logout(flask_restful.Resource):
    def post(self):
        cookie = authorization.delete_cookie()
        return 'Logging out', HTTPStatus.OK, {'Set-Cookie': cookie}
