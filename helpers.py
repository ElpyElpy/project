from re import S
from ssl import SSLSocket
from flask import redirect, render_template, request, session
from functools import wraps
from dbconnect import create_db_connection, execute_query, execute_query_adr, read_query_adr, read_query
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
from cgfunctions import usd, cg_get_data, percent
import jinja2


# This function checks registration form parameters
def complete_registration(user_name, password, confirmation, connection):

    if user_name == "" or user_name == None:
        alert = "user name can not be empty"
        return render_template("register.html", alert=alert)

    if password == "" or password == None:
        alert = "password can not be empty"
        return render_template("register.html", alert=alert)

    if len(password) < 8 or len(password) > 32:
        alert = "password must contain from 8 to 32 characters"
        return render_template("register.html", alert=alert)

    if confirmation == "" or confirmation == None or confirmation != password:
        alert = "pwd and pwd confirmation are different"
        return render_template("register.html", alert=alert)

    # Create quiery in DB to check if user exists
    names = read_query_adr(
        connection, "SELECT * FROM Users WHERE username = %s", (user_name,))
    if len(names) > 0:
        alert = "user already exists"
        return render_template("register.html", alert=alert)

    # Query to db to insert new user
    execute_query_adr(
        connection, "INSERT INTO Users (username, pwd) VALUES (%s, %s)", (user_name, generate_password_hash(password)))

    # Receive data from db to auto-login user
    user = read_query_adr(
        connection, "SELECT id, username, pwd FROM Users WHERE username=%s", (user_name,))

    # Check if user in db has the same pwd as registered user (user[0][2] - user pwd from db)
    if not check_password_hash(user[0][2], password):
        alert = "Smth went wrong"
        return render_template("register.html", alert=alert)

    # Save user_id (user[0][0] - unique user id from db)
    session["user_id"] = user[0][0]
    session["nick_name"] = user_name

    return render_template("main_page.html", username=session["nick_name"])


# This function checks registration form parameters
def complete_login(user_name, password, connection):

    # Ensure username was submitted
    if not user_name:
        alert = "Missing name"
        return render_template("login.html", alert=alert)

    # Ensure password was submitted
    if not password:
        alert = "missing password"
        return render_template("login.html", alert=alert)

    # Receive data from db to auto-login user
    user = read_query_adr(
        connection, "SELECT id, username, pwd FROM Users WHERE username=%s", (user_name,))

    # Check if user in db has the same pwd as registered user (user[0][2] - user pwd from db)
    if len(user) != 1 or not check_password_hash(user[0][2], password):
        alert = "wrong password"
        return render_template("login.html", alert=alert)

    # Save user_id (user[0][0] - unique user id from db)
    session["user_id"] = user[0][0]
    session["nick_name"] = user_name

    return render_template("main_page.html")


def login_required(f):
    """
    Decorate routes to require login.
    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @ wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def save_last_quote(user_id, symbol, price, connection):

    # save data after quotation, this data will be used for buying tokens
    quotes = read_query_adr(
        connection, "SELECT user_id, symbol FROM quotes WHERE user_id=%s", (user_id,))

    # only one row per user_id - it stores latest transaction
    if len(quotes) == 1:
        execute_query_adr(connection, "UPDATE quotes SET user_id = %s, symbol = %s, price = %s WHERE user_id = %s",
                          (user_id, symbol, float(price), user_id))
    else:
        execute_query_adr(connection, "INSERT INTO quotes (user_id, symbol, price) VALUES (%s, %s, %s)",
                          (user_id, symbol, float(price)))


def buy_tokens(tokens_to_add, connection):

    # check if number of tokens isn't negative or isn't zero

    # calculate sum of transaction
    last_quotation = read_query_adr(
        connection, "SELECT user_id, symbol, price FROM quotes WHERE user_id=%s", (session["user_id"],))
    price = last_quotation[0][2]
    symbol = last_quotation[0][1]
    tnx_sum = float(tokens_to_add) * float(price)

    # check if user has sufficient balance
    current_balance = read_query_adr(
        connection, "SELECT balance FROM Users WHERE id=%s", (session["user_id"],))
    current_balance = float(current_balance[0][0])
    if tnx_sum > current_balance:
        error_msg = "insufficient balance"
        return error_msg

    # update users balance and add tokens to the portfolio
    execute_query_adr(connection, "UPDATE Users SET balance = %s WHERE id = %s",
                      ((current_balance - tnx_sum), session["user_id"]))

    execute_query_adr(connection, "INSERT INTO transactions (user_id, symbol, buy_price, quantity, time_stamp) VALUES (%s, %s, %s, %s, %s)",
                      (session["user_id"], symbol, price, tokens_to_add, datetime.datetime.now()))

    token_data = read_query_adr(
        connection, "SELECT user_id, symbol, quantity, avg_price FROM portfolio WHERE user_id=%s AND symbol=%s", (session["user_id"], symbol))

    if len(token_data) > 0:
        new_price = (token_data[0][3] * token_data[0][2] + price *
                     float(tokens_to_add)) / (token_data[0][2] + float(tokens_to_add))
        execute_query_adr(connection, "UPDATE portfolio SET quantity = %s, avg_price = %s WHERE user_id = %s AND symbol = %s",
                          ((token_data[0][2] + float(tokens_to_add)), new_price, session["user_id"], symbol))
    else:
        execute_query_adr(connection, "INSERT INTO portfolio (user_id, symbol, quantity, avg_price) VALUES (%s, %s, %s, %s)",
                          (session["user_id"], symbol, float(tokens_to_add), price))


def get_user_portfolio(connection, user_id):
    balance = read_query_adr(
        connection, "SELECT symbol, quantity, avg_price FROM portfolio WHERE user_id=%s", (user_id,))
    portfolio = []
    if len(balance) < 1:
        return 1, 1
    # calculate initial AUM for total AUM change
    tokens_initial_aum = 0

    initial_balance = balance
    for asset in initial_balance:
        asset = list(asset)
        asset.append(float(asset[2]) * float(asset[1]))
        tokens_initial_aum = tokens_initial_aum + asset[3]
    total_initial_aum = get_cash(connection, user_id) + tokens_initial_aum

    # calculate data for table w/ portfolio and current AUM for total AUM change
    tokens_current_aum = 0
    for asset in balance:
        token_data = cg_get_data(asset[0])
        asset = list(asset)
        asset[2] = float(token_data["last_price"].replace(
            "$", "").replace(",", ""))
        asset.append(
            float(asset[1]) * float(asset[2]))
        portfolio.append(asset)
        tokens_current_aum = tokens_current_aum + asset[3]
    total_current_aum = get_cash(connection, user_id) + tokens_current_aum

    change = (total_current_aum - total_initial_aum) / (total_initial_aum)

    return portfolio, change


def get_cash(connection, user_id):
    cash = read_query_adr(
        connection, "SELECT balance FROM Users WHERE id=%s", (user_id,))
    return float(cash[0][0])


def get_user_transactions(connection, user_id):
    # get tnx data from DB
    transactions = read_query_adr(
        connection, "SELECT symbol, quantity, buy_price, time_stamp FROM transactions WHERE user_id=%s", (session["user_id"],))

    return transactions
