from flask import Flask


def init_app(test_config=None):
    """
    Implements the standard Flask Application Factory design pattern.
    From https://hackersandslackers.com/flask-application-factory/.
    """
    # create app
    app = Flask(__name__, instance_relative_config=False)

    # self-contain app context
    with app.app_context():

        # include defined routes
        from . import routes
        return app
