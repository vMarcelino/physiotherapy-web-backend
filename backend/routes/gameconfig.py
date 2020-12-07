from http import HTTPStatus
from typing import Optional
import flask_restful
from werkzeug.exceptions import abort
from backend import helper_functions
from backend import database
from backend import jwt_classes
from backend.jwt_classes import access_levels
import json


class GameConfig(flask_restful.Resource):
    @helper_functions.args_from_urlencoded
    @helper_functions.inject_user_from_authorization
    def get(self, authorization: database.Authorization, patient_token: jwt_classes.Patient[access_levels.Id]):
        if not isinstance(authorization.owner, database.Professional):
            return 'Only professionals are allowed to access this resource', HTTPStatus.FORBIDDEN
        professional: database.Professional = authorization.owner
        q = database.Patient.query
        q = q.join(database.Patient._links)
        q = q.filter(database.Link.professional == professional)
        q = q.filter(database.Patient.id == patient_token._id)
        patient: Optional[database.Patient] = q.one_or_none()

        if patient is None:
            return 'Patient not found', HTTPStatus.NOT_FOUND

        return patient.game_config, HTTPStatus.OK

    @helper_functions.args_from_json
    @helper_functions.inject_user_from_authorization
    def post(self, authorization: database.Authorization, patient_token: jwt_classes.Patient[access_levels.Id],
             parameters: dict):
        if not isinstance(authorization.owner, database.Professional):
            return 'Only professionals are allowed to access this resource', HTTPStatus.FORBIDDEN
        professional: database.Professional = authorization.owner
        q = database.Patient.query
        q = q.join(database.Patient._links)
        q = q.filter(database.Link.professional == professional)
        q = q.filter(database.Patient.id == patient_token._id)
        patient: Optional[database.Patient] = q.one_or_none()

        if patient is None:
            return 'Patient not found', HTTPStatus.NOT_FOUND

        patient.game_config = json.dumps(parameters)
        sess = database.db.session
        sess.add(patient)
        sess.commit()
        return 'ok', HTTPStatus.OK


class PatientGameConfig(flask_restful.Resource):
    @helper_functions.args_from_urlencoded
    @helper_functions.inject_user_from_authorization
    def get(self, authorization: database.Authorization):
        if not isinstance(authorization.owner, database.Patient):
            return 'Only patients are allowed to access this resource', HTTPStatus.FORBIDDEN
        patient: database.Patient = authorization.owner

        return patient.game_config, HTTPStatus.OK