from backend.jwt_classes.access_levels import AccessLevels
from backend.helper_functions import first_or_abort
import flask_restful
import flask
from typing import Callable, List, Optional, Sequence, Dict, Any, Union
from http import HTTPStatus
import json
from backend import helper_functions
from backend import database as db
from backend import jwt_classes


class ProfessionalLinking(flask_restful.Resource):
    @helper_functions.args_from_json
    @helper_functions.inject_user_from_authorization
    def post(self, authorization: db.Authorization, cpf: str):
        if not isinstance(authorization.owner, db.Professional):
            return 'Only professionals are allowed to access this resource', HTTPStatus.FORBIDDEN
        professional: db.Professional = authorization.owner
        patient: Optional[db.Patient] = db.Patient.query.filter(db.Patient.cpf == cpf).one()

        if not patient:
            return 'Patient not found', HTTPStatus.NOT_FOUND

        previous_link_q = db.Link.query
        previous_link_q = previous_link_q.filter(db.Link.patient_id == patient.id)
        previous_link_q = previous_link_q.filter(db.Link.professional_id == professional.id)
        previous_link: Optional[db.Link] = previous_link_q.one_or_none()
        if previous_link is not None:
            return 'Invite already exists', HTTPStatus.CONFLICT

        link = db.Link(patient=patient, professional=professional)
        db.db.session.add(link)
        db.db.session.commit()
        return 'Invite created', HTTPStatus.OK

    @helper_functions.args_from_urlencoded
    @helper_functions.inject_user_from_authorization
    def get(self, authorization: db.Authorization):
        if not isinstance(authorization.owner, db.Professional):
            return 'Only professionals are allowed to access this resource', HTTPStatus.FORBIDDEN
        professional: db.Professional = authorization.owner
        return [{'token': t.patient.to_jwt(subject=authorization)} for t in professional.links]
