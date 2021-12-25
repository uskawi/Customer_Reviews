import os
from datetime import datetime
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)


app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)


@app.route("/")
@app.route("/home")
def home():
    users = mongo.db.users.find()
    return render_template("home.html", users=users)


def time_to_string():
    '''
    convert datetime object to string using datetime.strftime()
    this part of code is credited to thispointer.com
    url ("https://thispointer.com/python-how-to-convert
    -datetime-object-to-string-using-datetime-strftime/")
    '''
    date_time_obj = datetime.now()
    time_str = date_time_obj.strftime("%d-%b-%Y %H:%M")

    return time_str


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
