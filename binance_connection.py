import nest_asyncio
nest_asyncio.apply()
import time
from binance.streams import ThreadedWebsocketManager
from binance.spot import Spot
import utils
from datetime import datetime

def query_binance_status():
    """checks for connection error"""

    status = Spot().system_status()
    if status['status'] == 0:
        return True
    else:
        raise ConnectionError

def websocket_connection(ticker, api_key, api_secret):
    twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
    twm.start()

    def handle_socket_message(msg):
        print(f"message type: {msg['e']}")
        print(msg)

    twm.start_depth_socket(callback=handle_socket_message, symbol=ticker)

    # twm.join()

    time.sleep(10)
    twm.stop()

def submit_binance_trade(client, symbol, type, side, timeInForce, csv_path, csv_name, timestamp = datetime.now().timestamp()*1000, quantity = None, price = None, stopPrice = None):
    if type == 'LIMIT' or type == 'LIMIT_MAKER':
        order = client.create_order(symbol = symbol, type = type, side = side, timestamp = timestamp, timeInForce= timeInForce, quantity = quantity, price = price)
    elif type == 'STOP_LOSS' or type == 'STOP_LOSS_LIMIT' or type == 'TAKE_PROFIT' or type == 'TAKE_PROFIT_LIMIT':
        order = client.create_order(symbol = symbol, type = type, side = side, timestamp = timestamp, timeInForce= timeInForce, quantity = quantity, stopPrice = stopPrice, price = price)
    else:
        order = client.create_order(symbol = symbol, type = type, side = side, timestamp = timestamp, timeInForce= timeInForce, quantity = quantity)
    utils.write_to_csv(order, csv_path, csv_name)