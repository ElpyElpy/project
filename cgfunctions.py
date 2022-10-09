import imp
from flask import redirect, render_template, request, session
from functools import wraps
from dbconnect import create_db_connection, execute_query, execute_query_adr, read_query_adr, read_query
from werkzeug.security import check_password_hash, generate_password_hash
from pycoingecko import CoinGeckoAPI
import pandas as pd
import logging
import time
from datetime import datetime
import cryptowatch as cw
import jinja2
import os
import requests as req
import json


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"


jinja2.filters.FILTERS['usd'] = usd


def qnt(value):
    return f"{value:,.2f}"


def percent(value):
    """Format value as percent."""
    if value > 0:
        return f"+{value*100:,.2f}%"
    elif value < 0:
        return f"{value*100:,.2f}%"
    return f"{value:,.2f}%"


jinja2.filters.FILTERS['percent'] = percent


def cg_check_connection():
    # check connection with coingecko
    if "(V3)" in cg.ping()["gecko_says"]:
        logging.critical('CONNECTED WITH COINGECKO')


def get_api_key():
    if 'RDS_DB_NAME' in os.environ:
        return os.environ["CW_TOKEN"]
    else:
        return "Token"


def cg_get_data(symbol):
    token_data = {}
    symbol = symbol.lower()
    cw.api_key = get_api_key()
    curr = "usdt"
    # exchanges = ['binance:', 'coinbase-pro:']
    # exchanges = ['coinbase-pro:', 'binance:']
    exchanges = ['coinbase-pro:', 'binance:', 'ftx:', 'binance-us:', 'huobi:', 'kraken:',
                 'uniswap-v2:', 'dex-aggregated:', 'bitflyer:', 'bittrex:', 'gemini:',
                 'luno:', 'gateio:', 'bitfinex:', 'cexio:', 'bisq:', 'bitmex:', 'okex:',
                 'liquid:', 'quoine:', 'bitbay:', 'hitbtc:', 'poloniex:', 'bitstamp:',
                 'bitz:', 'bithumb:', 'coinone:', 'okcoin:', 'dummy-exchange:']
    # exchange = 'coinbase-pro:'
    for exchange in exchanges:
        pair = exchange + symbol + curr
        token = cw.assets.get(symbol)
        try:
            summary = cw.markets.get(pair)
        except:
            if exchange == exchanges[-1]:
                token_data = 'There are no pair with usdt'
                return token_data

            continue

        # get main symbol statistics
        token_data["name"] = token.asset.name
        token_data["last_price"] = usd(summary.market.price.last)
        token_data["lowest_price"] = usd(summary.market.price.low)
        token_data["highest_price"] = usd(summary.market.price.high)
        token_data["change24h"] = percent(summary.market.price.change)
        token_data["volume"] = usd(summary.market.volume_quote)
        token_data["symbol"] = symbol.upper()
        token_data["price_db"] = summary.market.price.last

        return token_data


def cg_hist_price(symbol, time_delta=None):
    symbol = symbol.lower()
    # load api
    cw.api_key = get_api_key()
    curr = "usdt"
    # exchanges = ['coinbase-pro:', 'binance:']
    exchanges = ['coinbase-pro:', 'binance:', 'ftx:', 'binance-us:', 'huobi:', 'kraken:',
                 'uniswap-v2:', 'dex-aggregated:', 'bitflyer:', 'bittrex:', 'gemini:',
                 'luno:', 'gateio:', 'bitfinex:', 'cexio:', 'bisq:', 'bitmex:', 'okex:',
                 'liquid:', 'quoine:', 'bitbay:', 'hitbtc:', 'poloniex:', 'bitstamp:',
                 'bitz:', 'bithumb:', 'coinone:', 'okcoin:']
    for exchange in exchanges:
        pair = exchange + symbol + curr
        try:
            candles = cw.markets.get(pair, ohlc=True)
        except:
            continue

        if time_delta == None:
            fr = 1000 - 24 * 7
            to = 1000
            candles = candles.of_1h[fr:to]
        elif time_delta.total_seconds() < 3600:
            fr = 1000 - int(round(time_delta.total_seconds()/60, 0)) - 2
            to = 1000
            candles = candles.of_1m[fr:to]
        elif time_delta.total_seconds() < 12 * 3600:
            fr = 1000 - int(round(time_delta.total_seconds()/180, 0)) - 2
            to = 1000
            candles = candles.of_3m[fr:to]
        elif time_delta.total_seconds() < 24 * 3600:
            fr = 1000 - int(round(time_delta.total_seconds()/300, 0)) - 2
            to = 1000
            candles = candles.of_5m[fr:to]
        else:
            fr = 1000 - int(round(time_delta.total_seconds()/3600, 0)) - 2
            to = 1000
            candles = candles.of_1h[fr:to]
        # get historical data
        cg_prices = []
        cg_labels = []
        for candle in candles:
            cg_prices.append(candle[1])
            cg_labels.append(datetime.utcfromtimestamp(
                int(candle[0])).strftime('%Y-%m-%d %H:%M:%S'))

        return cg_prices, cg_labels


def cg_get_portfolio_history(connection, balance, cash, user_id):
    # get prices for each crypto assets inside of users portfolio
    temp = []
    # get time-stamp for the earliest tnx
    time_stamps = read_query_adr(
        connection, "SELECT * FROM transactions WHERE user_id = %s", (user_id,))
    time_delta = datetime.now() - time_stamps[0][4]
    for asset in balance:
        cg_prices, cg_labels = cg_hist_price(asset[0], time_delta)
        cg_prices = [element * float(asset[1].replace(",", ""))
                     for element in cg_prices]
        if len(temp) == 0:
            temp = cg_prices
        else:
            temp = [sum(x) for x in zip(temp, cg_prices)]
    cg_prices = [element + float(cash.replace(",", "").replace("$", ""))
                 for element in temp]
    return cg_prices, cg_labels


def cg_get_token_list():
    # connect to cw and construct API request
    api_key = get_api_key()
    request_link = "https://api.cryptowat.ch/assets?" + api_key
    all_symbols = []

    # request all token data
    result = req.get(request_link).text
    jResult = json.loads(result)

    # format requested data as a list
    for el in jResult["result"]:
        all_symbols.append(el['symbol'])

    return all_symbols
