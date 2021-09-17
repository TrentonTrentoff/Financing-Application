import os
from cs50 import SQL

from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Connect SQLITE3 to finance database
db = SQL("sqlite:///finance.db")

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

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]
    # Checks database for users purchase history
    stockowned = db.execute("SELECT * FROM history WHERE userID = ? AND shares > 0", user_id)
    for stock in stockowned:
        currentprice = lookup(stock["stock"])
        # Adds extra elements to list returned from lookup function, adding currrent price and value for the user
        stock["currentprice"] = currentprice["price"]
        stock["portfoliovalue"] = (stock["currentprice"]) * stock["shares"]
    # Finds current balance of user
    currentcash = db.execute("SELECT cash FROM users WHERE ID = ?", user_id)
    totalvalue = sum(item['portfoliovalue'] for item in stockowned)
    currentcash = currentcash[0]['cash']
    totalvalue = currentcash + totalvalue
    return render_template("index.html", stockowned=stockowned, currentcash=currentcash, totalvalue=totalvalue)

@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    if request.method=="POST":
        user_id = session["user_id"]
        if not request.form.get("password"):
            return apology("must provide password", 400)

        # Checks if user password matches confirmation  
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)
        
        hashpassword = generate_password_hash(request.form.get("password"))
        # Updates the database with new user password
        db.execute("UPDATE users SET hash = ? WHERE id = ?", hashpassword, user_id)
        return redirect("/")

    if request.method=="GET":
        return render_template("password.html")

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method=="POST":
        stock = lookup(request.form.get("symbol"))
        if not stock:
            return apology("No amount of stock chosen")
        if not request.form.get("shares").isnumeric():
            return apology("Invalid text entered")
        if float (request.form.get("shares")) < 0:
            return apology("Negative text entered")
        stockprice = stock["price"]
        stocksymbol = stock["symbol"]
        amount = request.form.get("shares")
        user_id = session["user_id"]
        dateTimeObj = datetime.now()
        cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
        cash = cash[0]['cash']
        # Checks if current balance is higher than purchase price, returns apology if not
        if (int (amount) * stockprice > int (cash)):
            return apology("You can't afford this")
        cost = int (amount) * stockprice
        moneyremaining = int(cash) - cost
        ## Update cash in database with cash remaining
        db.execute("UPDATE users SET cash = ? WHERE id = ?", moneyremaining, user_id)
        db.execute("INSERT INTO purchases (userID, stock, shares, price, type, time) VALUES(?, ?, ?, ?, ?, ?)", user_id, stocksymbol, amount, stockprice, "Bought", dateTimeObj)
        rows = db.execute("SELECT * FROM history WHERE userID = ? AND stock = ?", user_id, stocksymbol)
        # Checks to see if stock has been purchased before, updates history if so, creates new row in history if now
        if len(rows) == 1:
            currentshares = db.execute("SELECT shares FROM history WHERE userID = ? AND stock = ?", user_id, stocksymbol)
            currentshares = currentshares[0]['shares']
            newshares = int (currentshares) + int (amount)
            db.execute("UPDATE history SET shares = ? WHERE userID = ? AND stock = ?", newshares, user_id, stocksymbol)
            return redirect("/")
        else:
            db.execute("INSERT INTO history (userID, stock, shares) VALUES(?, ?, ?)", user_id, stocksymbol, amount)
            return redirect("/")


    if request.method=="GET":
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    user_id = session["user_id"]
    purchasehistory = db.execute("SELECT stock, shares, price, type, time FROM purchases WHERE userID = ?", user_id)
    return render_template("history.html", purchasehistory=purchasehistory)

@app.route("/addcash", methods=["GET", "POST"])
@login_required
def addcash():
    user_id = session["user_id"]
    
    # Check for user input of cash
    extracash = request.form.get("cash")
    
    # Ensure a number was submitted
    if not extracash.isnumeric():
        return apology("Invalid amount entered")
    
    # Ensure a positive was submitted
    if float (extracash) < 0:
        return apology("Negative amount entered")
    
    # Checks database for current balance, adds extra cash onto current balance
    currentcash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
    currentcash = currentcash[0]['cash']
    newcash = float(currentcash) + float (extracash)
    db.execute("UPDATE users SET cash = ? WHERE id = ?", newcash, user_id)
    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST
    if request.method == "POST":

        # Ensure username was submitted
        username = request.form["username"]
        if not username:
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form["password"]:
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", (username,),)
        # Ensure username exists and password is correct
        if len(rows) != 1:
            return apology("invalid username", 400)
        if not check_password_hash(rows[0]['hash'], request.form["password"]):
            return apology("invalid password", 400)

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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        stock = request.form.get("symbol")
        stock = lookup(stock)
        if not stock:
            return apology("Stock lookup failed")
        return render_template("quoted.html", stock=stock)

    if request.method == "GET":
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            return apology("must provide username", 400)
        rowtest = db.execute("SELECT * FROM users WHERE username = ?", (username,),)
        if len(rowtest) == 1:
            return apology("username already exists!", 400)

        if not request.form.get("password"):
            return apology("must provide password", 400)

        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, generate_password_hash(request.form.get("password")))
        return redirect("/login")

    elif request.method == "GET":
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("No stock chosen", 400)
        if not request.form.get("shares"):
            return apology("No amount chosen", 400)
        user_id = session["user_id"]
        dateTimeObj = datetime.now()
        amount = request.form.get("shares")
        stock = request.form.get("symbol")
        amountofstocks = db.execute("SELECT shares FROM history WHERE userID = ? AND stock = ?", user_id, stock)
        amountofstocks = amountofstocks[0]['shares']
        if int (amount) > int (amountofstocks):
            return apology("selling more stocks than currently owned", 400)
        currentstatus = lookup(stock)
        value = float (currentstatus["price"]) * int (amount)
        existingcash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
        existingcash = existingcash[0]['cash']
        newcash = existingcash + value
        db.execute("UPDATE users SET cash = ? WHERE id = ?", newcash, user_id)
        newamountofstocks = int (amountofstocks) - int(amount)
        stockprice = currentstatus["price"]
        db.execute("UPDATE history SET shares = ? WHERE userID = ? AND stock = ?", newamountofstocks, user_id, stock)
        db.execute("INSERT INTO purchases (userID, stock, shares, price, type, time) VALUES(?, ?, ?, ?, ?, ?)", user_id, stock, amount, stockprice, "Sold", dateTimeObj)
        return redirect("/")

    if request.method == "GET":
        user_id = session["user_id"]
        stockowned = db.execute("SELECT stock FROM history WHERE userID = ? AND shares > 0", user_id)
        return render_template("sell.html", stockowned=stockowned)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
