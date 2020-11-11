import flask
import flask_restful
from travel_backpack.decorators import decorate_all_methods

from backend import helper_functions
from backend.routes.access_test import AccessTest

from backend.routes.login import Login
from backend.routes.logout import Logout

from backend.routes.signup import Signup

from backend.routes.user import User

api = flask_restful.Api()

docs = {}


def add_resource(resource, *routes):
    """Adds the resource and also adds the session_remove decorator
    """
    session_remover_class_decorator = decorate_all_methods(helper_functions.session_remove)
    resource = session_remover_class_decorator(resource)
    api.add_resource(resource, *routes)


def add_api_resource(resource, *routes):
    doc_route = routes[0]
    docs[doc_route] = resource
    return add_resource(resource, *['/api/v1' + route for route in routes])

# api routes
add_api_resource(Signup, '/signup')
add_api_resource(Login, '/login')
add_api_resource(Logout, '/logout')

add_api_resource(User, '/user')

add_api_resource(AccessTest, '/accesstest')


def init_app(app):
    api.init_app(app)
