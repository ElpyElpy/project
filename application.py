import os
import logging
from flask import Flask, flash, redirect, render_template, request, session, json
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import complete_registration, complete_login, login_required
from cgfunctions import cg_get_data, cg_hist_price
from dbconnect import create_db_connection, execute_query
from datetime import datetime

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
    logging.critical('ENVIRONMENT CREDENTIAL VARS IN USE')
    RDS_HOSTNAME = os.environ["RDS_HOSTNAME"]
    RDS_USERNAME = os.environ["RDS_USERNAME"]
    RDS_PASSWORD = os.environ["RDS_PASSWORD"]
    RDS_DB_NAME = os.environ["RDS_DB_NAME"]
    connection = create_db_connection(
        RDS_HOSTNAME, RDS_USERNAME, RDS_PASSWORD, RDS_DB_NAME)
else:
    logging.critical('LOCAL CREDENTIAL VARS IN USE')
    RDS_HOSTNAME = "awseb-e-ntynzp3uin-stack-awsebrdsdatabase-iapnb6lobbke.cxksdtctbisg.us-east-1.rds.amazonaws.com"
    RDS_USERNAME = "DBPortfolioGames"
    RDS_PASSWORD = "London2022!!"
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


@application.route("/buy", methods=["GET", "POST"])
def create_portfolio():
    # in case of post request, get token data (prompted by user) from coingecko and then represent it on web page
    if request.method == "POST":
        token_data = cg_get_data(request.form.get("symbol"))
        cg_prices, cg_labels = cg_hist_price(request.form.get("symbol"))
        cg_prices = json.dumps(cg_prices)
        cg_labels = json.dumps(cg_labels)
        return render_template("buy.html", token_name=token_data["name"], token_symbol=token_data["symbol"], token_price=token_data["price"], token_mcap=token_data["mcap"], token_vol24=token_data["volume24"], token_change24=token_data["change24"], cg_prices=cg_prices, cg_labels=cg_labels)

    # in case of get request, get BTC token data from coingecko and then represent it on web page
    token_data = cg_get_data("BTC")
    cg_prices, cg_labels = cg_hist_price("BTC")
    cg_prices = json.dumps(cg_prices)
    cg_labels = json.dumps(cg_labels)

    return render_template("buy.html", token_name=token_data["name"], token_symbol=token_data["symbol"], token_price=token_data["price"], token_mcap=token_data["mcap"], token_vol24=token_data["volume24"], token_change24=token_data["change24"], cg_prices=cg_prices, cg_labels=cg_labels)
    # return render_template("buy.html")


if __name__ == "__main__":
    application.debug = True
    application.run()
