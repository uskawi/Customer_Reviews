""" import """
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
    """ home page """
    hottest_companies = mongo.db.companies.find().sort(
            "reviews_count", -1).limit(3)
    company_counter = 0
    return render_template("home.html",
                           hottest_companies=hottest_companies,
                           company_counter=company_counter)


@app.route("/views_hottest_companies/<company_name>")
def views_hottest_companies(company_name):
    """ Hottest companies"""
    company = mongo.db.companies.find_one({"company_name": company_name})
    reviews = list(mongo.db.reviews.find({"company_name": company_name}))
    return render_template("search_results.html",
                           company=company, reviews=reviews)


@app.route("/for_business")
def for_business():
    """ for businesses page """
    return render_template("for_business.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """ register page """
    if request.method == "POST":
        #  creating date varibale
        time_created = time_to_string()
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
    """ Login page """
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
                flash("Incorrect Email or Password", "category1")
        else:
            # username doesn't exist
            flash("Incorrect Email or Password", "category1")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route('/logout')
def logout():
    """ Logout """
    flash("You have been logged out", "category1")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    """ Profile page """
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    user = mongo.db.users.find_one({"username": username})

    if session["user"]:
        return render_template("profile.html", user=user)

    return redirect(url_for("login"))


@app.route("/search", methods=["GET", "POST"])
def search():
    """ company search """

    query = request.form.get("company-name")
    companies = list(mongo.db.companies.find({"$text": {"$search": query}}))
    return render_template(
        "companies_results.html", companies=companies, query=query)


@app.route("/reviews_results/<company_id>", methods=["POST", "GET"])
def reviews_results(company_id):
    """ View reviews """
    company = mongo.db.companies.find_one({"_id": ObjectId(company_id)})
    reviews = list(mongo.db.reviews.find({"company_id": ObjectId(company_id)}))
    company_score = avrage_score(reviews, "score")
    if reviews:
        for review in reviews:
            review["username"] = ""
            for key, value in review.items():
                if key == "user_id":
                    user = mongo.db.users.find_one(
                        {"_id": ObjectId(value)})
                    if user:
                        user_name = user = mongo.db.users.find_one(
                            {"_id": ObjectId(value)})["username"]
                        review["username"] = user_name
                    else:
                        review["username"] = "User"

    return render_template("reviews_results.html", company=company,
                           reviews=reviews, company_score=company_score)


@app.route("/add_review/<company_id>", methods=["POST", "GET"])
def add_review(company_id):
    """ add review page """
    # creating date varibale
    time_created = time_to_string()
    company = mongo.db.companies.find_one(
            {"_id": ObjectId(company_id)})
    if request.method == "POST":
        reviews_count = company["reviews_count"]
        company_id = company["_id"]
        user_id = mongo.db.users.find_one({"username": session["user"]})["_id"]
        added_review = {
            "user_id": user_id,
            "company_id": company_id,
            "time_created": time_created,
            "score": int(request.form.get("score")),
            "review_content": request.form.get("review-text"),
            "review_title": request.form.get("title"),
        }
        # add reviews counter to reviewed company
        new_review_count = {
                "$set": {
                    "reviews_count": reviews_count + 1
                    }
                }
        mongo.db.reviews.insert_one(added_review)
        mongo.db.companies.update_one(
            {"_id": company_id}, new_review_count)
        flash("Review Added successfully.", "category2")
        return render_template("messages.html")

    return render_template("add_review.html", company=company)


@app.route("/add_company", methods=["POST", "GET"])
def add_company():
    """ Add company page """
    # creating date varibale
    time_created = time_to_string()
    user_id = mongo.db.users.find_one({"username": session["user"]})["_id"]
    if session['user'] and request.method == "POST":
        added_company = {
            "user_id": user_id,
            "company_name": request.form.get("company-name").lower(),
            "date_created": time_created,
            "description": request.form.get("description"),
            "reviews_count": 0
        }
        mongo.db.companies.insert_one(added_company)
        flash("Company Added successfully.", "category2")
        return render_template("messages.html")
    return render_template("add_company.html")


@app.route("/edit_review/<review_id>", methods=["GET", "POST"])
def edit_review(review_id):
    """ Edit review page """
    time_updated = time_to_string()
    if request.method == "POST":
        tobe_updated = {
            "$set": {
                "time_updated": time_updated,
                "score": int(request.form.get("score")),
                "review_content": request.form.get("review-text"),
                "review_title": request.form.get("title")
                }
            }
        mongo.db.reviews.update_many(
            {"_id": ObjectId(review_id)}, tobe_updated)
        flash("Review updated successfully.", "category1")
    review = mongo.db.reviews.find_one({"_id": ObjectId(review_id)})
    return render_template("edit_review.html", review=review)


@app.route("/delete_review/<review_id>")
def delete_review(review_id):
    """ Edit review page """
    company_id =  mongo.db.reviews.find_one({"_id": ObjectId(review_id)})["company_id"]
    reviews_count = mongo.db.companies.find_one(
            {"_id": ObjectId(company_id)})["reviews_count"] 
    # add reviews counter to reviewed company
    new_review_count = {
            "$set": {
                "reviews_count": reviews_count - 1
                }
            }

    mongo.db.companies.update_one(
        {"_id": company_id}, new_review_count)
    flash("Review Successfully Removed", "category2")
    mongo.db.reviews.delete_one({"_id": ObjectId(review_id)})
    return render_template("messages.html")


@app.route("/delete_user/<user_id>")
def delete_user(user_id):
    """ Edit review page """
    mongo.db.users.delete_one({"_id": ObjectId(user_id)})
    # mongo.db.reviews.db.romove({"user_id": user_id})
    flash("Account Deleted Successfuly", "category3")
    session.pop("user")
    return redirect(url_for("home"))


@app.route("/edit_user/<user_id>", methods=["POST", "GET"])
def edit_user(user_id):
    """ Edit user """
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    old_username = user["username"]
    time_updated = time_to_string()
    if request.method == "POST":
        username = request.form.get("username").lower()
        email = request.form.get("email")
        existing_username = mongo.db.users.find_one(
            {"username": username})
        existing_email = mongo.db.users.find_one({"email": email})
        if not existing_username and not existing_email:

            update_user = {
                "$set": {
                    "time_updated": time_updated,
                    "username": username,
                    "email": email,
                    }
                }
            mongo.db.users.update_many(
                {"_id": ObjectId(user_id)}, update_user)
            # update username in all reviews added by the update_user
            reviews_added_by_update_user = {
                "$set": {
                    "username": username,
                    }
                }
            mongo.db.reviews.update_many(
                {"username": old_username}, reviews_added_by_update_user)
            session.pop("user")
            flash(
                "User name and email updated successfully."
                "Please login again.",
                "category1")
            return redirect(url_for("login"))

        elif not existing_username and existing_email:

            update_user = {
                "$set": {
                    "time_updated": time_updated,
                    "username": username,
                    }
                }
            mongo.db.users.update_many(
                {"_id": ObjectId(user_id)}, update_user)
            # update username in all reviews added by the update_user
            reviews_added_by_update_user = {
                "$set": {
                    "username": username,
                    }
                }
            mongo.db.reviews.update_one(
                {"username":  old_username}, reviews_added_by_update_user)
            session.pop("user")
            flash("Username updated successfully. Please login again.",
                  "category1")
            return redirect(url_for("login"))

        if existing_username and not existing_email:

            update_user = {
                "$set": {
                    "time_updated": time_updated,
                    "email": email,
                    }
                }
            mongo.db.users.update_many(
                {"_id": ObjectId(user_id)}, update_user)
            flash(
                "email updated successfully. Please login again.",
                "category1")
            return redirect(url_for("login"))

        else:
            flash("Sorry but we could't update your details", "category1")
            return redirect(url_for("edit_user",
                            user=user, user_id=user["_id"]))

    return render_template("edit_user.html", user=user)


@app.route("/edit_password/<user_id>", methods=["POST", "GET"])
def edit_password(user_id):
    """ Edit password """
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    time_updated = time_to_string()
    old_password = "password"
    if request.method == "POST":
        new_password = request.form.get("password")
        if new_password != old_password:
            update_password = {
                "$set": {
                    "time_updated": time_updated,
                    "password": generate_password_hash(
                                request.form.get("password"))
                    }
                }
            mongo.db.users.update_one(
                {"_id": ObjectId(user_id)}, update_password)
            session.pop("user")
            flash(
                "User password updated successfully."
                "Please login again.",
                "category1")
            return redirect(url_for("login"))
        else:
            flash(
                "We couldn't updated your password.", "category1")
            return redirect(url_for("edit_password",
                            user=user, user_id=user["_id"]))
    return render_template("edit_password.html", user=user)


def time_to_string():
    '''
    convert datetime object to string using datetime.strftime()
    this part of code is credited to thispointer.com
    url ("https://thispointer.com/python-how-to-convert
    -datetime-object-to-string-using-datetime-strftime/")
    '''
    date_time_obj = datetime.now()
    time_str = date_time_obj.strftime("%d-%b-%Y  (%H:%M)")

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
