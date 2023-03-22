import nest_asyncio
nest_asyncio.apply()
import time
from binance.streams import ThreadedWebsocketManager
from binance.spot import Spot

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

