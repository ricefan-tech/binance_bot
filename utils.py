import datetime

from binance.spot import Spot
import pandas as pd
import json
import os
from binance.client import Client
import csv
from pathlib import Path

ENUM_DEFINITIONS = {
    'type': ['LIMIT', 'MARKET', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT', 'LIMIT_MAKER'],
    'timeinForce': ['GTC', 'IOC', 'FOK']
}

ORDER_SPECIFICS = {
    'MARKET': [('quantity', 'quoteOrderQty')],
    'LIMIT': ['timeInForce', 'quantity', 'price'],
    'STOP_LOSS': ['stopPrice', 'quantity', 'price'],
    'STOP_LOSS_LIMIT': ['timeInForce', 'quantity', 'price', ('stopPrice', 'trailingDelta')],
    'TAKE_PROFIT': ['quantity', ('stopPrice', 'trailingDelta')],
    'TAKE_PROFIT_LIMIT': ['timeInForce', 'quantity', 'price', ('stopPrice', 'trailingDelta')],
    'LIMIT_MAKER': ['quantity', 'price']
}

def get_project_settings(importFilepath):
    """import binance keys from settings file"""

    if os.path.exists(importFilepath):
        f = open(importFilepath, "r")
        project_settings = json.load(f)
        f.close()
        return project_settings
    else:
        return ImportError

def get_candlestick_data(ticker, timeframe, qty):
    """query raw candlestick data"""

    raw_data = Spot().klines(symbol=ticker, interval=timeframe, limit=qty)
    converted_data = []
    for candle in raw_data:
        converted_candle = {
            'time': candle[0],
            'open': float(candle[1]),
            'high': float(candle[2]),
            'low': float(candle[3]),
            'close': float(candle[4]),
            'volume': float(candle[5]),
            'close_time': candle[6],
            'quote_asset_volume': float(candle[7]),
            'number_of_trades': int(candle[8]),
            'taker_buy_base_asset_volume': float(candle[9]),
            'taker_buy_quote_asset_volume': float(candle[10])
        }
        converted_data.append(converted_candle)
    return converted_data


def get_and_transform_binance_data(ticker, timeframe, qty):
    """get raw candlestick data and put in panda"""

    raw_data = get_candlestick_data(ticker=ticker, timeframe=timeframe, qty=qty)
    df_data = pd.DataFrame(raw_data)
    df_data['time'] = pd.to_datetime(df_data['time'], unit='ms')
    df_data['close_time'] = pd.to_datetime(df_data['close_time'], unit='ms')
    return df_data


def query_spot_asset_list(quote_ticker):
    """Get current spot price for list of tickers"""

    ticker_dictionary = Spot().ticker_price
    ticker_dataframe = pd.DataFrame(ticker_dictionary['symbols'])
    quote_ticker_dataframe = ticker_dataframe.loc[ticker_dataframe['quoteAsset'].isin(quote_ticker)]
    quote_ticker_dataframe = quote_ticker_dataframe.loc[quote_ticker_dataframe['status'] == "TRADING"]
    return quote_ticker_dataframe


def get_historical_data(client, ticker, start_date, end_date):
    """Get historic data for given period length and ticker"""

    print(f"Getting data for {ticker}")

    candle = client.get_historical_klines(ticker, Client.KLINE_INTERVAL_30MINUTE, str(start_date), str(end_date))
    df = pd.DataFrame(candle,
                      columns=['dateTime', 'open', 'high', 'low', 'close', 'volume', 'closeTime', 'quoteAssetVolume',
                               'numberOfTrades', 'takerBuyBaseVol', 'takerBuyQuoteVol', 'ignore'])
    df['dateTime'] = pd.to_datetime(df.dateTime, unit='ms')
    df['dateTime_str'] = df.dateTime.dt.strftime("%Y-%m-%d %H-%M-%S")
    # df.set_index('dateTime', inplace=True)
    df = df.drop(['closeTime', 'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol', 'takerBuyQuoteVol', 'ignore'],
                 axis=1)
    df.open = df.open.astype(float)
    df.high = df.high.astype(float)
    df.low = df.low.astype(float)
    df.close = df.close.astype(float)
    df.volume = df.volume.astype(float)
    return df


def get_return_per_interval(x, cols):
    """calculate returns over different columns"""

    for c in cols:
        x[f"{c}_return"] = (x[c] - x[c].shift(1)) / x[c].shift(1)
    return x


def get_trade_pnl(price, signal):
    """calculates return per trade"""

    n, t, result = 0, 0, []
    for p, s in zip(price, signal):
        if s == 1:
            n, t = n + 1, t + p
            yield 0
        elif s == 0:
            yield 0
        elif s == -1:
            avg = t / n
            n, t = n - 1, t - avg
            yield p - avg
        else:
            assert s in (1, 0, -1), f"Signal {s} error"


def get_trade_pnl_per_ticker(df, buy, sell, considered_price):
    """calculates return per trade per ticker"""

    print(f'pnl_{buy}_{sell}')
    df[f'pnl_{buy}_{sell}'] = list(get_trade_pnl(df[considered_price], df[f'trade_{buy}_{sell}']))
    return df

def is_valid_order(symbol, side, type, timestamp, **kwargs):
    """verifies that passed parameters are valid for the desired order type"""

    if symbol is None or side is None or type is None or timestamp is None:
        raise ValueError("Invalid order, all orders must have symbol, side, type and timestamp.")
    if type not in ORDER_SPECIFICS.keys():
        raise ValueError("Invalid order type.")

    for mandatory_field in ORDER_SPECIFICS[type]:
        if isinstance(mandatory_field, tuple):
            field_1 = mandatory_field [0]
            field_2 = mandatory_field[1]
            if field_1 not in kwargs and field_2 not in kwargs:
                return False
        else:
            if mandatory_field not in kwargs:
                return False
    return True

def write_to_csv(data, csv_path, csv_name):
    """Writes trade outputs into specified CSV or creates new if not existent"""
    path = Path(csv_path)
    path.mkdir(parents=True, exist_ok= True)
    with open(f'{csv_path}/{csv_name}.csv', 'a', newline='') as my_file:
        csv_writer = csv.DictWriter(my_file, data)
        csv_writer.writeheader()
        csv_writer.writerow(data)
        print(f"Successfully written data into file {csv_path}.")

