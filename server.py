import os
from typing import Callable

import flask
import flask_cors

import backend
from backend.constants import CONSTANTS


def create_application():
    custom_db = os.getenv('SQLALCHEMY_DATABASE_URI', '').lower()

    # create app
    application = flask.Flask(__name__, template_folder='./frontend/build', static_folder='./frontend/build/static')

    # configure app
    if custom_db:
        application.config['SQLALCHEMY_DATABASE_URI'] = custom_db
        print('Custom db set!')

    else:
        dbnfo = CONSTANTS.database_info
        connection_string = f'mysql+pymysql://{dbnfo.user}:{dbnfo.password}@{dbnfo.host}/{dbnfo.database}'
        application.config['SQLALCHEMY_DATABASE_URI'] = connection_string

    application.config['SQLALCHEMY_ECHO'] = False
    application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    flask_cors.CORS(application)

    # initialize routes, extensions, everything
    backend.initialize(application)

    @application.route('/', defaults={'path': ''})
    @application.route('/<path:path>')
    def root(path):
        if path != "" and os.path.exists(application.template_folder + '/' + path):
            return flask.send_from_directory(application.template_folder, path)
        else:
            return flask.render_template('index.html')

    return application


def main():
    create_application().run(host='0.0.0.0', port=5000, debug=False)


if __name__ == "__main__":
    main()


def create_OAS():
    create_application()
    from backend.helper_functions.decorators import _extracted_docs
    from backend.routes import docs
    from pprint import pprint
    import yaml

    conf = {
        "swagger": "2.0",
        "host": "localhost:5000",
        "schemes": ["https", "http"],
        "basePath": "/api/v1",
        "tags": [],
        "paths": {},
        "info": {
            "title": "Physiotherapy platform backend api doc",
            "version": "1.0.0"
        }
    }
    for path, resource in docs.items():
        class_name = resource.__name__
        class_module = resource.__module__
        conf['tags'].append({"name": class_name})
        conf["paths"][path] = {}
        if class_module in _extracted_docs and class_name in _extracted_docs[class_module]:
            for method in _extracted_docs[class_module][class_name]:
                ed = _extracted_docs[class_module][class_name][method]
                conf["paths"][path][method] = ed
                if 'responses' not in conf["paths"][path][method] or len(conf["paths"][path][method]['responses']) == 0:
                    conf["paths"][path][method]['responses'] = {"400": {"description": "missing fields"}}
                conf["paths"][path][method]['tags'] = [class_name]
                parameters = ed['parameters']
                if parameters and 'schema' in parameters[0]:
                    # print('has schema in parameters')
                    req = parameters[0]['schema']['required']
                    if not req:
                        # print('deleted')
                        del parameters[0]['schema']['required']

    with open('OAS.yml', 'w') as f:
        yaml.dump(conf, f)


def create_all():
    create_application().app_context().push()
    import backend.database as models
    db = models.db
    db.create_all()
   