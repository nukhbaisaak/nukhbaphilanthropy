import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///donations.db")

@app.route("/")
def index():
    """Show donation projects"""
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("Username required!")
        elif not password:
            return apology("Password required!")
        elif not confirmation:
            return apology("Please confirm password!")

        if password != confirmation:
            return apology("Passwords do not match")


        hash = generate_password_hash(password)

        try:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
            return redirect('/')
        except:
            return apology("Username has already been registered!")

    else:
        return render_template("register.html")

@app.route("/aboutus")
def aboutus():
    """Show about us"""
    return render_template("aboutus.html")

@app.route("/fundings")
def fundings():
    """Show where we fund"""
    return render_template("fundings.html")


@app.route("/donate", methods=["GET", "POST"])
@login_required
def donate():
    """Donate money to Nukhba Philanthropy"""
    if request.method == "POST":
        amount = int(request.form.get("amount"))
        cause = request.form.get("cause")


        if not amount:
            return apology("Please enter an amount you want to donate")

        if amount <= 0:
            return apology("Please enter a valid amount to donate")

        user_id = session["user_id"]
        cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]

        if cash < amount:
            return apology("Not enough cash!")
        else:
            db.execute("UPDATE users SET cash = ? WHERE id = ?", cash - amount, user_id)
            db.execute("INSERT INTO transactions (user_id, amount, cause) VALUES (?, ?, ?)",
            user_id, amount, cause)

        return redirect('/thankyou')
    else:
        return render_template("donate.html")

@app.route("/thankyou")
def thankyou():
    """Thank the user for donation"""
    return render_template("thankyou.html")


@app.route("/how-we-work")
def howwework():
    """How we work """
    return render_template("how-we-work.html")




@app.route("/newsletter", methods=["GET", "POST"])
def newsletter():
    """Subscribe to Newsletter"""
    if request.method == "POST":
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        email = request.form.get("email")
        organisation = request.form.get("organisation")

        if not firstname:
            return apology("First name required")

        if not email:
            return apology("Email required")

        else:
            db.execute("INSERT INTO newsletter (firstname, lastname, email, organisation) VALUES (?, ?, ?, ?)", firstname, lastname, email, organisation)

        return redirect('/subscription-success')

    else:
        return render_template("newsletter.html")

@app.route("/subscription-success")
def subscription():
    """Thank the user for subscribing"""
    return render_template("subscription-success.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

@app.route("/donations")
@login_required
def donations():
    """Show donations of the user"""
    user_id = session["user_id"]

    donations = db.execute("SELECT cause, SUM(amount) as totalCauseDonations FROM transactions WHERE user_id = ? GROUP BY cause ", user_id)
    cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]
    totals =  db.execute("SELECT SUM(amount) as totalDonations FROM transactions WHERE user_id = ?", user_id)


    for total in totals:
        totalAmount = total["totalDonations"]

    return render_template("donations.html", totalAmount=totalAmount, donations=donations, total=total, cash=cash, usd=usd)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
