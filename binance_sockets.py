from datetime import datetime

import sys
#from binance.websockets import BinanceSocketManager
from binance import ThreadedWebsocketManager
import config


_socket_client = None
_socket_key = None
_socket_depths = {}
dfd = {}
print(type(_socket_depths))
_symbols = []

DEPTH_SYMBOL_SUFFIX = '@depth5'

def stop():
    _socket_client.stop_socket(_socket_key)


def on_receive_depths(msg):
    """
    Receives single Binance socket event.
    If the event tops up to all numbers of symbols, to start format events
    """

    global _socket_depths
    global dfd

    if not msg['stream'].endswith(DEPTH_SYMBOL_SUFFIX):
        print('skip socket message')
        return

    symbol = msg['stream'][:-len(DEPTH_SYMBOL_SUFFIX)]
    
    _socket_depths[symbol] = {'symbol': symbol, 'data': msg['data']}

    if len(_socket_depths.keys()) == len(_symbols):
        result = format_depths(_socket_depths.values(), _symbols)
        _socket_depths = {}
        return result


def format_depths(socket_depths, symbols):
    """
    Parses the order books,
    gets the worst price and the total amount of all orders
    """

    result = []
    for depth in socket_depths:
        data = depth['data']
        symbol = depth['symbol'].upper()

        bids_quantity = sum([float(amount) for amount, _ in data['bids']])
        bids_price = float(data['bids'][-1][0])

        asks_quantity = sum([float(amount) for amount, _ in data['asks']])
        asks_price = float(data['asks'][-1][0])

        result.append({
            'symbol': symbol,
            'bids': {
                'price': bids_price,
                'quantity': bids_quantity
            },
            'asks': {
                'price': asks_price,
                'quantity': asks_quantity
            }
        })

    return sorted(result, key=lambda depth: symbols.index(depth['symbol']))


def start_depths_socket(client, symbols, callback):
    """
    Initiates the binance socket connect.
    Binds socket received messages to the external callback
    """

    global _symbols
    global _socket_client
    global _socket_key

    _symbols = symbols

    _socket_client = ThreadedWebsocketManager(config.get('api_key'),config.get('api_secret'))
    _socket_client.start()

    symbols_websockets = [(s + DEPTH_SYMBOL_SUFFIX).lower() for s in _symbols]
    #symbols_websockets = ['ethusdt@depth5', 'btcusdt@depth5']


    # internal... ugly.. but wraps the external callback in this scope
    def socket_cb(msg):
        #print(msg)
        depths = on_receive_depths(msg)
        #print(depths)
        if depths:
            callback(depths)


    # _socket_client.start_multiplex_socket(
    #     symbols_websockets,
    #     socket_cb)

    def handle_socket_message(msg):
        #print(f"message type: {msg['e']}")
        print(msg)

    #twm.start_kline_socket(callback=handle_socket_message, symbol=symbol)

    # multiple sockets can be started
    #twm.start_depth_socket(callback=handle_socket_message, symbol=symbol)

    # or a multiplex socket can be started like this
    # see Binance docs for stream names
    _socket_client.start_multiplex_socket(callback=socket_cb, streams=symbols_websockets)


if __name__ == '__main__':
    import time
    
    import binance_client

    symbols = binance_client.get_symbols(*config.get('markets'))

    _socket_depths = {}

    def dummy_callback(depths):
        print('dummy callback', depths)

    #customStream(binance_client.get_client())
    start_depths_socket(binance_client.get_client(), symbols, dummy_callback)

    while True:
        time.sleep(5)
        continue
