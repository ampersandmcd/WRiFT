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

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/problem")
def problem():
    return render_template("problem.html")

@app.route("/resources")
def resources():
    return render_template("resources.html")

@app.route("/solution")
def solution():
    return render_template("solution.html")