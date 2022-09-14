from flask import redirect, render_template, request, session
from functools import wraps
from dbconnect import create_db_connection, execute_query, execute_query_adr, read_query_adr, read_query
from werkzeug.security import check_password_hash, generate_password_hash


# This function checks registration form parameters
def complete_registration(user_name, password, confirmation, connection):

    # Ensure username was submitted
    if not user_name:
        print(f"username: {user_name}")
        alert = "missing name"
        return render_template("register.html", alert=alert)

    # Ensure password was submitted
    if not password:
        alert = "missing password"
        return render_template("register.html", alert=alert)

    # Ensure passwords are the same
    if password != confirmation:
        alert = "pwds different"
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

    return render_template("main_page.html")


# This function checks registration form parameters
def complete_login(user_name, password, connection):

    # Ensure username was submitted
    if not user_name:
        print(f"username: {user_name}")
        alert = "missing name"
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
        alert = "Wrong pwd"
        return render_template("login.html", alert=alert)

    # Save user_id (user[0][0] - unique user id from db)
    session["user_id"] = user[0][0]

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
