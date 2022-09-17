from flask import redirect, render_template, request, session, json
from functools import wraps
from dbconnect import create_db_connection, execute_query, execute_query_adr, read_query_adr, read_query
from werkzeug.security import check_password_hash, generate_password_hash
from pycoingecko import CoinGeckoAPI
import pandas as pd
import logging
import time
from datetime import datetime


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"


def percent(value):
    """Format value as percent."""
    return f"{value:,.2f}%"


def cg_check_connection():
    # check connection with coingecko
    if "(V3)" in cg.ping()["gecko_says"]:
        logging.critical('CONNECTED WITH COINGECKO')


def cg_get_data(symbol):
    cg = CoinGeckoAPI()
    token_data = {}
    symbol = symbol.lower()
    # receive all tokens data and get token price by symbol
    tokens = cg.get_coins_list()
    logging.critical('list of tokens was loaded')
    for token in tokens:
        if token["symbol"] == symbol:
            logging.critical('token was found by symbol')
            price = cg.get_price(token["id"], "usd", include_market_cap=True,
                                 include_24hr_vol=True, include_24hr_change=True)
            token_data["price"] = usd(price[token["id"]]["usd"])
            token_data["mcap"] = usd(price[token["id"]]["usd_market_cap"])
            token_data["volume24"] = usd(price[token["id"]]["usd_24h_vol"])
            token_data["change24"] = percent(
                price[token["id"]]["usd_24h_change"])
            token_data["name"] = token["name"]
            token_data["symbol"] = token["symbol"].upper()
            print(price)
            return token_data


def cg_hist_price(symbol):
    cg = CoinGeckoAPI()

    symbol = symbol.lower()
    # receive all tokens data and get token price by symbol
    tokens = cg.get_coins_list()
    logging.critical('list of tokens was loaded')
    for token in tokens:
        if token["symbol"] == symbol:
            logging.critical('token was found by symbol')

            # Calculate endPeriod in UNIX (now)
            endPeriod = int(time.time())

            # Calculate start period in UNIX (end period - 7 days time delta)
            time_delta = 6 * 24 * 60 * 60
            startPeriod = endPeriod - time_delta
            # receive historical data from CoinGecko
            data = cg.get_coin_market_chart_range_by_id(
                token["id"], "usd", startPeriod, endPeriod)

            # save only prices
            data = data["prices"]

            # save in json data, which will be placed into JS code (via jinja code)
            cg_prices = []
            cg_labels = []
            for el in data:
                cg_prices.append(el[1])
                cg_labels.append(datetime.utcfromtimestamp(
                    int(el[0])/1000).strftime('%Y-%m-%d'))

            # format unis time-stamps into dd/mm/yy format

            return cg_prices, cg_labels


# cg_prices, cg_labels = cg_hist_price("BTC")
# print(cg_prices)
# print("########")
# print(cg_labels)

# cg_prices, cg_labels = cg_hist_price("BTC")
# print(cg_prices)
# print(cg_labels)
