from backend.constants import CONSTANTS
import os
import backend.database
import backend.routes


def initialize(app, *others_to_initialize):
    if not os.path.isdir(CONSTANTS.video_folder):
        os.makedirs(CONSTANTS.video_folder)

    to_initialize = [backend.routes, backend.database, *others_to_initialize]
    for obj in to_initialize:
        obj.init_app(app)