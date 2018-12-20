from tests import ccxt


def get(exchange_name):
    return ccxt.Instance(exchange_name)




if __name__ == '__main__':
    exchange_name = "bitmex"

    _client = get(exchange_name)
    print(_client.fetch_ohlcv("BTC/USD", timeframe='1m',
                        limit=100,
                        params={"reverse": True}
                        ))

