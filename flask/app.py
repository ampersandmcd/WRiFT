from flask import Flask
from flask import render_template

app = Flask(__name__)


@app.route("/")
def index():
    """
    Instantiates a demo flask app.
    Open a powershell/cmd/terminal in `CapstoneExploration/flask` and run `flask run` for the demo.
    :return: HTML for the browser to render.
    """
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")
