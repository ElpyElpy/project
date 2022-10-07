from distutils.command.install_egg_info import safe_name
from http.client import CannotSendHeader
import os
import logging
from flask import Flask, flash, redirect, render_template, request, session, json
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import complete_registration, complete_login, login_required, buy_tokens, save_last_quote, get_user_portfolio, get_cash, get_user_transactions
from cgfunctions import cg_get_data, cg_hist_price, usd, qnt, cg_get_portfolio_history, percent
from dbconnect import create_db_connection, execute_query
from datetime import datetime
import jinja2

import mysql.connector
from mysql.connector import Error
import pandas as pd

application = Flask(__name__)

# Ensure templates are auto-reloaded
application.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
application.config["SESSION_PERMANENT"] = True
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
    RDS_HOSTNAME = "hostname"
    RDS_USERNAME = "username"
    RDS_PASSWORD = "pwd"
    RDS_DB_NAME = "db_name"
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
@login_required
def create_portfolio():
    # in case of post request, get token data (prompted by user) from coingecko and then represent it on web page
    if request.method == "POST":
        token_data = cg_get_data(request.form.get("symbol"))
        cg_prices, cg_labels = cg_hist_price(request.form.get("symbol"))
        cg_prices = json.dumps(cg_prices)
        cg_labels = json.dumps(cg_labels)

        # save search results into DB
        save_last_quote(session["user_id"],
                        token_data["symbol"], token_data["price_db"], connection)
        return render_template("buy.html", token_name=token_data["name"], token_symbol=token_data["symbol"], token_la_price=token_data["last_price"], token_lo_price=token_data["lowest_price"], token_hi_price=token_data["highest_price"], token_vol24=token_data["volume"], token_change24=token_data["change24h"], cg_prices=cg_prices, cg_labels=cg_labels)

    # in case of get request, get BTC token data from coingecko and then represent it on web page
    token_data = cg_get_data("BTC")
    cg_prices, cg_labels = cg_hist_price("BTC")
    cg_prices = json.dumps(cg_prices)
    cg_labels = json.dumps(cg_labels)

    # save search results into DB
    save_last_quote(session["user_id"],
                    token_data["symbol"], token_data["price_db"], connection)
    return render_template("buy.html", token_name=token_data["name"], token_symbol=token_data["symbol"], token_la_price=token_data["last_price"], token_lo_price=token_data["lowest_price"], token_hi_price=token_data["highest_price"], token_vol24=token_data["volume"], token_change24=token_data["change24h"], cg_prices=cg_prices, cg_labels=cg_labels)
    # return render_template("buy_copy.html")


@application.route("/add_to_portfolio", methods=["GET", "POST"])
@login_required
def add_token_to_portfolio():
    if request.method == "POST":
        # calculate sum of transaction
        # check in db if balance is sufficient
        # if balance is sufficient decrease balance and add tokens to portfolio

        result = buy_tokens(request.form.get("tokens_to_add"), connection)
        if result == "insufficient balance":
            return render_template("buy.html", result=result)

        # return show_portfolio()
        return redirect("/portfolio")


@application.route("/portfolio", methods=["GET", "POST"])
@login_required
def show_portfolio():
    # get data for portfolio table
    balance, change = get_user_portfolio(connection, session["user_id"])
    if balance == 1:
        return render_template("main_page.html", balance=balance)
    cash = get_cash(connection, session["user_id"])
    total = cash
    for asset in balance:
        total = total + float(asset[3])
        asset[1] = qnt(asset[1])
        asset[2] = usd(asset[2])
        asset[3] = usd(asset[3])
    total = usd(total)
    cash = usd(cash)

    # get data for AUM chart
    cg_prices, cg_labels = cg_get_portfolio_history(
        connection, balance, cash, session["user_id"])

    cg_prices = json.dumps(cg_prices)
    cg_labels = json.dumps(cg_labels)

    # calculate overall portfolio change
    total_change = change

    # get data for tnx table
    transactions = get_user_transactions(connection, session["user_id"])

    return render_template("portfolio.html", balance=balance, cash=cash, total=total, cg_prices=cg_prices, cg_labels=cg_labels, total_change=total_change, transactions=transactions)
    # return render_template("portfolio_copy.html", balance=balance, cash=cash, total=total)


if __name__ == "__main__":
    application.debug = True
    application.run()
