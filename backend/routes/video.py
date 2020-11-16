import flask
import flask_restful
from typing_extensions import Literal
from backend import jwt_classes
from backend.database import VideoInfo
from backend.helper_functions.decorators import inject_user_from_authorization
from backend.jwt_classes.access_levels import AccessLevels, Id
from backend.constants import CONSTANTS
from typing import Dict, List, Optional, Tuple, Union
from http import HTTPStatus

from backend import helper_functions
import backend.database as db


class Video(flask_restful.Resource):
    @helper_functions.args_from_urlencoded
    @inject_user_from_authorization
    def get(self, authorization: db.Authorization, video_id: int)->Union[ \
        Tuple[Literal['Video not found'], Literal[ HTTPStatus.NOT_FOUND]],
        flask.Response]:

        owner = authorization.owner
        video: Optional[db.VideoInfo]
        if isinstance(owner, db.Professional):
            q = db.VideoInfo.query
            q = q.join(db.VideoInfo.session)
            q = q.join(db.Session.patient)
            q = q.join(db.Patient.links)
            q = q.filter(db.VideoInfo.id == video_id)
            q = q.filter(db.Link.accepted == True)
            q = q.filter(db.Link.professional_id == owner.id)
            video = q.one_or_none()
        elif isinstance(owner, db.Patient):
            q = db.VideoInfo.query
            q = q.join(db.VideoInfo.session)
            q = q.filter(db.VideoInfo.id == video_id)
            q = q.filter(db.Session.patient_id == owner.id)
            video = q.one_or_none()
        else:
            raise Exception('Owner expected to be either Patient or Professional')

        if video is None:
            return 'Video not found', HTTPStatus.NOT_FOUND

        return flask.send_from_directory('./videos', video.path)


class PatientSessions(flask_restful.Resource):
    @helper_functions.args_from_urlencoded
    @inject_user_from_authorization
    def get(self, authorization: db.Authorization)->Union[ \
        Tuple[Literal['Only patients are allowed to access this resource'], Literal[ HTTPStatus.FORBIDDEN]],
        Tuple[Dict[str, List[Dict[str, int]]], Literal[HTTPStatus.OK]]]:

        owner = authorization.owner
        if not isinstance(owner, db.Patient):
            return 'Only patients are allowed to access this resource', HTTPStatus.FORBIDDEN

        patient = owner
        return {
            str(helper_functions.date_to_timestamp(session.date)): [{
                "id": video.id
            } for video in session.videos]
            for session in patient.sessions
        }, HTTPStatus.OK


class ProfessionalPatientSessions(flask_restful.Resource):
    @helper_functions.args_from_urlencoded
    @inject_user_from_authorization
    def get(self, authorization: db.Authorization, patient_token: jwt_classes.Patient[Id])->Union[ \
        Tuple[Literal['Only professionals are allowed to access this resource'], Literal[ HTTPStatus.FORBIDDEN]],
        Tuple[Literal['Patient not found'], Literal[HTTPStatus.NOT_FOUND]],
        Tuple[Dict[str, List[Dict[str, int]]], Literal[HTTPStatus.OK]]]:

        owner = authorization.owner
        if not isinstance(owner, db.Professional):
            return 'Only professionals are allowed to access this resource', HTTPStatus.FORBIDDEN

        professional = owner
        patient_q = db.Patient.query
        patient_q = patient_q.join(db.Patient.links)
        patient_q = patient_q.filter(db.Link.accepted == True)
        patient_q = patient_q.filter(db.Link.professional_id == professional.id)
        patient_q = patient_q.filter(db.Patient.id == patient_token._id)
        patient: Optional[db.Patient] = patient_q.one_or_none()
        if patient is None:
            return 'Patient not found', HTTPStatus.NOT_FOUND

        return {
            str(helper_functions.date_to_timestamp(session.date)): [{
                "id": video.id
            } for video in session.videos]
            for session in patient.sessions
        }, HTTPStatus.OK
