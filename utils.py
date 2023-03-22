from binance.spot import Spot
import pandas as pd
import json
import os

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


def get_historical_data(client, ticker):
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