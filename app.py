from flask import Flask, request, session, render_template
from cs50 import SQL

# initialize app
app = Flask(__name__)

# configure app
app.config["TEMPLATES_AUTO_RELOAD"] = True

# configure database
db = SQL("sqlite:///grades.db")

# app routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/add", methods=["GET", "POST"])
def add():
    return render_template("add.html")

@app.route("/grades", methods=["GET", "POST"])
def grades():
    return render_template("grades.html")

@app.route("/drop", methods=["GET", "POST"])
def drop():
    return render_template("drop.html")
