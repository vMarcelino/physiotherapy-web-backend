import flask_restful


class AccessTest(flask_restful.Resource):
    def get(self):
        return 'hi, this seems to be working now', 200