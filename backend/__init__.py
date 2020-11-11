import backend.database
import backend.routes

def initialize(app, *others_to_initialize):
    to_initialize = [backend.routes, backend.database, *others_to_initialize]
    for obj in to_initialize:
        obj.init_app(app)