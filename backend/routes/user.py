from backend.jwt_classes.access_levels import AccessLevels
from backend.helper_functions import first_or_abort
import flask_restful
import flask
from typing import Callable, List, Optional, Sequence, Dict, Any, Union
from http import HTTPStatus
import json
from backend import helper_functions
from backend import database
from backend import jwt_classes


class User(flask_restful.Resource):
    @helper_functions.args_from_urlencoded
    @helper_functions.inject_user_from_authorization
    def get(self, user_id: int):
        user: Optional[database.User] = database.User.get(user_id)
        if user is None:
            return "This user no long exists", HTTPStatus.UNAUTHORIZED

        return {'token': user.to_jwt(auth=False, subject=user_id)}, HTTPStatus.OK

    @helper_functions.args_from_json
    @helper_functions.inject_user_from_authorization
    def put(self, user_id: int, name: Optional[str] = None, email: Optional[str] = None):

        user: Optional[database.User] = database.User.query.get(user_id)
        if user is None:
            return "This user no long exists", HTTPStatus.UNAUTHORIZED

        changes = False
        if name is not None and name != user.name:
            changes = True
            user.name = name

        if email is not None and email != user.email:
            changes = True
            user_with_email = database.User.query.filter(database.User.email == email).one_or_none()
            if user_with_email:
                return 'Email already in use', HTTPStatus.CONFLICT
            else:
                user.email = email

        if changes:
            session = database.db.session
            session.add(user)
            session.commit()

            return {"message": 'User updated', "token": user.to_jwt(auth=False, subject=user_id)}, HTTPStatus.OK
        else:
            return {"message": 'No changes', "token": user.to_jwt(auth=False, subject=user_id)}, HTTPStatus.OK