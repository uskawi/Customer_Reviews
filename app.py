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
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        #  check if email already exists in db
        existing_user = mongo.db.users.find_one(
            {"email": request.form.get("email")})
        if existing_user:
            # check the password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = existing_user["username"]
                flash("Welcome, {}".format(existing_user["username"]),
                      "category1")
                return redirect(url_for(
                    "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Email and/or Password")
        else:
            # username doesn't exist
            flash("Incorrect Email and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route('/logout')
def logout():
    flash("You have been logged out",  "category1")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    # grab the session user's from db
    user = mongo.db.users.find_one(
        {"username": session["user"]})
    if session["user"]:
        return render_template(
            "profile.html", user=user,)

    return render_template(
        "profile.html", user=user)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("company-name")
    company = mongo.db.company.find_one(
           {"company_name": query.lower()})
    session["company_name"] = query.lower()
    if company:
        company_name = session["company_name"]
        review = list(mongo.db.review.find(
            {"company_name": company_name}))
        if review:
            company_score = avrage_score(review, "score")
            return render_template("home.html", review=review,
                                   company_score=company_score,
                                   company=company,
                                   company_name=session["company_name"])

        else:
            return render_template("home.html", company=company)

    flash("Ooops!!! We Couldn't Find Any Results For {}".format(query),
          "category2")
    return render_template("search_error.html")


@app.route("/add_review", methods=["POST", "GET"])
def add_review():
    # creating date varibale
    time_created = time_to_string()
    if session['user'] and request.method == "POST":
        added_review = {
            "username": session['user'],
            "company_name": session["company_name"],
            "time_created": time_created,
            "score": int(request.form.get("score")),
            "review_content": request.form.get("review-text"),
            "review_title": request.form.get("title")
        }
        mongo.db.review.insert_one(added_review)
        flash("Review Added successfully.", "category1")
        return redirect(url_for("add_review"))


    return render_template("add_review.html")



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


def avrage_score(arr, ind):
    '''
    Calculate The average sum of all scores
    '''
    count = 0
    total = 0
    if len(arr) > 0:
        for item in arr:
            if item[ind]:
                total += item[ind]
                count += 1

        return round(total/count, 1)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
