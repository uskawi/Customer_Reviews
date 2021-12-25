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


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        #  creating date varibale
        time_created = time_to_string()
        #  check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})
        #  check if email already exists in db
        existing_email = mongo.db.users.find_one(
            {"email": request.form.get("email")})

        if existing_user or existing_email:
            flash("Username or Email already in use",  "category1")
            return redirect(url_for('register'))

        register_user = {
            "username": request.form.get("username").lower(),
            "email": request.form.get("email").lower(),
            "password": generate_password_hash(
                request.form.get("password")),
            "time_created": time_created
        }
        mongo.db.users.insert_one(register_user)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration succesful", "category1")
        return redirect(url_for("home", username=session["user"]))

    return render_template("register.html")


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
