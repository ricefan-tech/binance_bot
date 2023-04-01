import json
import os
import pandas as pd
import numpy as np
import asyncio
import websockets
import plotly.express as px
from datetime import datetime
import seaborn as sns
from binance.spot import Spot
from binance.client import Client
import pandas as pd
import datetime, time
import itertools
import time
import binance_connection as api
import utils

import_filepath = ""
csv_folder_path = ""

project_settings = utils.get_project_settings(import_filepath)
api_key = project_settings['BinanceKeys']['API_Key']
api_secret = project_settings['BinanceKeys']['Secret_Key']
historical_days = 30
end_date = datetime.datetime(2023,3,21,20,58)
start_date = end_date - datetime.timedelta(days = historical_days)

if __name__ == '__main__':

    client = Client(api_key, api_secret)
    client.API_URL = 'https://api.binance.com/api'
    assert(api.query_binance_status() == True)

    # getting live stream
    #api.websocket_connection('BTCBUSD', api_key, api_secret)

    # getting info for ticker orders and sending test order -- valid order returns empty dict
    #info = client.get_symbol_info('SHIBBUSD')

    symbol = 'CFXBUSD'
    side = 'BUY'
    type = 'LIMIT'
    price = 0.09
    quantity = 300
    timeinForce = 'GTC'
    info = client.get_symbol_info(symbol)
    print(info)
    api.submit_binance_trade(client = client, symbol = symbol, side = side, type = type, price = price, quantity= quantity, timeInForce=timeinForce, csv_path=csv_folder_path, csv_name='submitted_orders')
    #order = client.order_limit_buy(symbol = symbol, side = side, type = type, timestamp = timestamp, price = price, quantity = quantity)
