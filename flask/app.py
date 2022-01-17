from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello_world():
    """
    Instantiates a demo flask app.
    Open a powershell/cmd/terminal in `CapstoneExploration/flask` and run `flask run` for the demo.
    :return: HTML for the browser to render.
    """
    return "<p>Hello, World!</p>" \
           "<p>Team Anthropocene Institute checking in, ready to roll.</p>" \
           "<p>Check out <a href=https://flask.palletsprojects.com/en/2.0.x/quickstart/>this page</a> " \
           "for more information on the basics of Flask.</p>"
