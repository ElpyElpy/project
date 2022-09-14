import os
import logging
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import complete_registration, complete_login
from dbconnect import create_db_connection, execute_query

import mysql.connector
from mysql.connector import Error
import pandas as pd

application = Flask(__name__)

# Ensure templates are auto-reloaded
application.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
application.config["SESSION_PERMANENT"] = False
application.config["SESSION_TYPE"] = "filesystem"
Session(application)

if 'RDS_DB_NAME' in os.environ:
    logging.warning('ENVIRONMENT CREDENTIAL VARS IN USE')
    print(f"ENVIRONMENT CREDENTIAL VARS IN USE")
    RDS_HOSTNAME = os.environ["RDS_HOSTNAME"]
    print(f"HOSTNAME: {RDS_HOSTNAME}")
    RDS_USERNAME = os.environ["RDS_USERNAME"]
    print(f"USERNAME: {RDS_USERNAME}")
    RDS_PASSWORD = os.environ["RDS_PASSWORD"]
    print(f"PWD: {RDS_PASSWORD}")
    RDS_DB_NAME = os.environ["RDS_DB_NAME"]
    print(f"DB NAME: {RDS_DB_NAME}")
    connection = create_db_connection(
        RDS_HOSTNAME, RDS_USERNAME, RDS_PASSWORD, RDS_DB_NAME)
else:
    logging.warning('LOCAL CREDENTIAL VARS IN USE')
    RDS_HOSTNAME = ""
    RDS_USERNAME = ""
    RDS_PASSWORD = ""
    RDS_DB_NAME = "ebdb"
    connection = create_db_connection(
        RDS_HOSTNAME, RDS_USERNAME, RDS_PASSWORD, RDS_DB_NAME)


@application.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@application.route("/")
def main_page():
    return render_template("main_page.html")


@application.route("/register", methods=["GET", "POST"])
def register():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Check registration parameters and complete registration
        return complete_registration(request.form.get("username"), request.form.get("password"), request.form.get("confirmation"), connection)

    return render_template("register.html")


@application.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    if request.method == "POST":
        # Check registration parameters and complete registration
        return complete_login(request.form.get("username"), request.form.get("password"), connection)

    return render_template("login.html")


@application.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


if __name__ == "__main__":
    application.debug = True
    application.run()
