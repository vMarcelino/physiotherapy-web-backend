from backend.constants import CONSTANTS
import os
from backend.routes import TokenObject
from typing import Literal, TypedDict
from backend.jwt_classes.access_levels import AccessLevels, Id
from backend.helper_functions import first_or_abort
import flask_restful
import flask
from typing import Callable, List, Optional, Sequence, Dict, Any, Tuple, Union
from http import HTTPStatus
import json
from backend import helper_functions
from backend.helper_functions import time as helper_functions_time
from backend import database as db
from backend import jwt_classes
import base64
import cv2
import uuid
import numpy as np


class PatientLinking(flask_restful.Resource):
    @helper_functions.args_from_json
    @helper_functions.inject_user_from_authorization
    def post(self, authorization: db.Authorization, professional_token: jwt_classes.Professional[Id], accept: bool)->Union[ \
        Tuple[Literal['Only patients are allowed to access this resource'], Literal[HTTPStatus.FORBIDDEN]],
        Tuple[Literal['Professional not found'], Literal[HTTPStatus.NOT_FOUND]],
        Tuple[Literal['Invite not found'], Literal[HTTPStatus.NOT_FOUND]],
        Tuple[Literal['Professional already linked'], Literal[HTTPStatus.CONFLICT]],
        Tuple[Literal['Invite updated'], Literal[HTTPStatus.OK]],
        ]:
        if not isinstance(authorization.owner, db.Patient):
            return 'Only patients are allowed to access this resource', HTTPStatus.FORBIDDEN
        patient: db.Patient = authorization.owner
        professional: Optional[db.Professional] = db.Professional.get(professional_token._id)

        if not professional:
            return 'Professional not found', HTTPStatus.NOT_FOUND

        link = helper_functions.first_or_abort(
            (l for l in patient._links if l.professional_id == professional_token._id), 'Invite not found')
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
    def get(self, authorization: db.Authorization)->Union[ \
        Tuple[Literal['Only patients are allowed to access this resource'], Literal[HTTPStatus.FORBIDDEN]],
        Tuple[List[TokenObject], Literal[HTTPStatus.OK]],
        ]:
        if not isinstance(authorization.owner, db.Patient):
            return 'Only patients are allowed to access this resource', HTTPStatus.FORBIDDEN
        patient: db.Patient = authorization.owner

        def make_result(link: db.Link) -> TokenObject:
            jwt = link.professional.to_jwt(subject=authorization, access_level=AccessLevels.personal)
            return {'token': jwt}

        return [make_result(link) for link in patient.invites], HTTPStatus.OK


class PatientVideoInput(flask_restful.Resource):
    @helper_functions.inject_user_from_authorization
    def post(self, authorization: db.Authorization):
        if not isinstance(authorization.owner, db.Patient):
            return 'Only patients are allowed to access this resource', HTTPStatus.FORBIDDEN
        patient: db.Patient = authorization.owner
        now = helper_functions.datetime_now()

        output_filename = str(uuid.uuid4()) + '-'
        count = 0
        make_filename = lambda: output_filename + str(count) + '.mp4'
        while os.path.isfile(os.path.join(CONSTANTS.video_folder, make_filename())):
            count += 1
        output_filename = make_filename()

        requestDict = flask.request.form.to_dict()
        print(requestDict.keys())
        data = []
        for key, value in requestDict.items():
            if 'frame' in key:
                img_data = base64.b64decode(value)
                nparr = np.fromstring(img_data, np.uint8)  # type: ignore
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                # cv2.imshow('', img)
                # cv2.waitKey(0)
                data.append(img)

        height, width, channels = data[0].shape

        # Define the codec and create VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Be sure to use lower case
        out = cv2.VideoWriter(os.path.join(CONSTANTS.video_folder, output_filename), fourcc, 30, (width, height))

        for image in data:
            out.write(image)  # Write out frame to video

        out.release()

        now = helper_functions.datetime_now()
        video_info = db.VideoInfo(path=output_filename, date=now, patient=patient)

        sess = db.db.session
        sess.add(video_info)
        sess.commit()

        return 'OK'