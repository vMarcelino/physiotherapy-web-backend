import datetime
import flask
import flask_restful
from typing import Literal
from backend import jwt_classes
from backend.database import VideoInfo
from backend.helper_functions.decorators import inject_user_from_authorization
from backend.jwt_classes.access_levels import AccessLevels, Id
from backend.constants import CONSTANTS
from typing import Dict, List, Optional, Tuple, Union
from http import HTTPStatus
from backend.helper_functions import time as helper_functions_time

from backend import helper_functions
import backend.database as db


class Video(flask_restful.Resource):
    @helper_functions.args_from_urlencoded
    @inject_user_from_authorization
    def get(self, authorization: db.Authorization, video_id: int)->Union[ \
        Tuple[Literal['Video not found'], Literal[HTTPStatus.NOT_FOUND]],
        flask.Response
        ]:

        owner = authorization.owner
        video: Optional[db.VideoInfo]
        if isinstance(owner, db.Professional):
            q = db.VideoInfo.query
            q = q.join(db.VideoInfo.patient)
            q = q.join(db.Patient._links)
            q = q.filter(db.VideoInfo.id == video_id)
            q = q.filter(db.Link.accepted == True)
            q = q.filter(db.Link.professional_id == owner.id)
            video = q.one_or_none()

        elif isinstance(owner, db.Patient):
            q = db.VideoInfo.query
            q = q.filter(db.VideoInfo.id == video_id)
            q = q.filter(db.VideoInfo.patient_id == owner.id)
            video = q.one_or_none()
        else:
            raise Exception('Owner expected to be either Patient or Professional')

        if video is None:
            return 'Video not found', HTTPStatus.NOT_FOUND

        return flask.send_from_directory(CONSTANTS.video_folder, video.video_path)

    @helper_functions.args_from_urlencoded
    @inject_user_from_authorization
    def delete(self, authorization: db.Authorization, video_id: int)->Union[ \
        Tuple[Literal['Video not found'], Literal[HTTPStatus.NOT_FOUND]],
        Tuple[Literal['Video deleted'], Literal[HTTPStatus.OK]],
        ]:

        owner = authorization.owner
        video: Optional[db.VideoInfo]
        if isinstance(owner, db.Professional):
            q = db.VideoInfo.query
            q = q.join(db.VideoInfo.patient)
            q = q.join(db.Patient._links)
            q = q.filter(db.VideoInfo.id == video_id)
            q = q.filter(db.Link.accepted == True)
            q = q.filter(db.Link.professional_id == owner.id)
            video = q.one_or_none()

        elif isinstance(owner, db.Patient):
            q = db.VideoInfo.query
            q = q.filter(db.VideoInfo.id == video_id)
            q = q.filter(db.VideoInfo.patient_id == owner.id)
            video = q.one_or_none()
        else:
            raise Exception('Owner expected to be either Patient or Professional')

        if video is None:
            return 'Video not found', HTTPStatus.NOT_FOUND

        db.Session.delete(video)
        db.Session.commit()
        return 'Video deleted', HTTPStatus.OK


class Thumbnail(flask_restful.Resource):
    @helper_functions.args_from_urlencoded
    @inject_user_from_authorization
    def get(self, authorization: db.Authorization, video_id: int)->Union[ \
        Tuple[Literal['Thumb not found'], Literal[HTTPStatus.NOT_FOUND]],
        flask.Response
        ]:

        owner = authorization.owner
        video: Optional[db.VideoInfo]
        if isinstance(owner, db.Professional):
            q = db.VideoInfo.query
            q = q.join(db.VideoInfo.patient)
            q = q.join(db.Patient._links)
            q = q.filter(db.VideoInfo.id == video_id)
            q = q.filter(db.Link.accepted == True)
            q = q.filter(db.Link.professional_id == owner.id)
            video = q.one_or_none()

        elif isinstance(owner, db.Patient):
            q = db.VideoInfo.query
            q = q.filter(db.VideoInfo.id == video_id)
            q = q.filter(db.VideoInfo.patient_id == owner.id)
            video = q.one_or_none()
        else:
            raise Exception('Owner expected to be either Patient or Professional')

        if video is None:
            return 'Thumb not found', HTTPStatus.NOT_FOUND

        return flask.send_from_directory(CONSTANTS.thumbnail_folder, video.thumbnail_path)


class PatientSessions(flask_restful.Resource):
    @helper_functions.args_from_urlencoded
    @inject_user_from_authorization
    def get(self, authorization: db.Authorization, time_delta:float)->Union[ \
        Tuple[Literal['Only patients are allowed to access this resource'], Literal[HTTPStatus.FORBIDDEN]],
        Tuple[Dict[str, List[Dict[str, int]]], Literal[HTTPStatus.OK]]
        ]:

        now = helper_functions.datetime_now()
        today = helper_functions_time._datify(now) + datetime.timedelta(hours=time_delta)

        owner = authorization.owner
        if not isinstance(owner, db.Patient):
            return 'Only patients are allowed to access this resource', HTTPStatus.FORBIDDEN

        patient = owner
        videos = patient.videos
        days: Dict[datetime.datetime, List[int]] = {}
        for video in sorted(videos, key=lambda video_info: video_info.date):
            day = helper_functions_time._datify(video.date) + datetime.timedelta(hours=time_delta)
            if day not in days:
                days[day] = []
            days[day].append(video.id)

        return {
            str(helper_functions.datetime_to_timestamp(day)): [{
                "id": video_id
            } for video_id in video_ids]
            for day, video_ids in days.items()
        }, HTTPStatus.OK


class ProfessionalPatientSessions(flask_restful.Resource):
    @helper_functions.args_from_urlencoded
    @inject_user_from_authorization
    def get(self, authorization: db.Authorization, patient_token: jwt_classes.Patient[Id], time_delta:float)->Union[ \
        Tuple[Literal['Only professionals are allowed to access this resource'], Literal[HTTPStatus.FORBIDDEN]],
        Tuple[Literal['Patient not found'], Literal[HTTPStatus.NOT_FOUND]],
        Tuple[Dict[str, List[Dict[str, int]]], Literal[HTTPStatus.OK]]
        ]:

        owner = authorization.owner
        if not isinstance(owner, db.Professional):
            return 'Only professionals are allowed to access this resource', HTTPStatus.FORBIDDEN

        professional = owner
        patient_q = db.Patient.query
        patient_q = patient_q.join(db.Patient._links)
        patient_q = patient_q.filter(db.Link.accepted == True)
        patient_q = patient_q.filter(db.Link.professional_id == professional.id)
        patient_q = patient_q.filter(db.Patient.id == patient_token._id)
        patient: Optional[db.Patient] = patient_q.one_or_none()
        if patient is None:
            return 'Patient not found', HTTPStatus.NOT_FOUND

        videos = patient.videos
        days: Dict[datetime.datetime, List[int]] = {}
        for video in sorted(videos, key=lambda video_info: video_info.date):
            day = helper_functions_time._datify(video.date) + datetime.timedelta(hours=time_delta)
            if day not in days:
                days[day] = []
            days[day].append(video.id)

        return {
            str(helper_functions.datetime_to_timestamp(day)): [{
                "id": video_id
            } for video_id in video_ids]
            for day, video_ids in days.items()
        }, HTTPStatus.OK
