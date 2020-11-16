from backend.jwt_classes.access_levels import AccessLevels, Id
from backend.helper_functions import first_or_abort
import flask_restful
import flask
from typing import Callable, List, Optional, Sequence, Dict, Any, Union
from http import HTTPStatus
import json
from backend import helper_functions
from backend import database as db
from backend import jwt_classes


class PatientLinking(flask_restful.Resource):
    @helper_functions.args_from_json
    @helper_functions.inject_user_from_authorization
    def post(self, authorization: db.Authorization, professional_token: jwt_classes.Professional[Id], accept: bool):
        if not isinstance(authorization.owner, db.Patient):
            return 'Only patients are allowed to access this resource', HTTPStatus.FORBIDDEN
        patient: db.Patient = authorization.owner
        professional: Optional[db.Professional] = db.Professional.get(professional_token._id)

        if not professional:
            return 'Professional not found', HTTPStatus.NOT_FOUND

        link = helper_functions.first_or_abort((l for l in patient._links), 'Invite not found')
        if link.accepted:
            return 'Professional already linked', HTTPStatus.CONFLICT

        if accept:
            link.accepted = True
            db.db.session.add(link)
        else:
            db.db.session.delete(link)
        db.db.session.commit()
        return 'Invite updated', HTTPStatus.OK

    @helper_functions.args_from_urlencoded
    @helper_functions.inject_user_from_authorization
    def get(self, authorization: db.Authorization):
        if not isinstance(authorization.owner, db.Patient):
            return 'Only patients are allowed to access this resource', HTTPStatus.FORBIDDEN
        patient: db.Patient = authorization.owner
        return [{
            'token': t.professional.to_jwt(subject=authorization, access_level=AccessLevels.personal)
        } for t in patient.invites]
