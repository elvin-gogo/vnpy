
def fetch_orders(self, symbol=None, since=None, limit=None, params={}):
    self.load_markets()
    market = None
    request = {}
    if symbol is not None:
        market = self.market(symbol)
        request['symbol'] = market['id']
    if since is not None:
        request['startTime'] = self.iso8601(since)
    if limit is not None:
        request['count'] = limit
    request = self.deep_extend(request, params)
    # why the hassle? urlencode in python is kinda broken for nested dicts.
    # E.g. self.urlencode({"filter": {"open": True}}) will return "filter={'open':+True}"
    # Bitmex doesn't like that. Hence resorting to self hack.
    if 'filter' in request:
        request['filter'] = self.json(request['filter'])
    response = self.privateGetOrder(request)
    return self.parse_orders(response, market, since, limit)


'''
def fetch_my_trades(self, symbol=None, limit=None, params={"reverse": True}):
    self.load_markets()
    market = None
    request = {}
    if symbol is not None:
        market = self.market(symbol)
        request['symbol'] = market['id']
    if since is not None:
        request['startTime'] = self.iso8601(since)
    if limit is not None:
        request['count'] = limit
    request = self.deep_extend(request, params)
     if 'filter' in request:
        request['filter'] = self.json(request['filter'])
    response = self.privateGetExecutionTradeHistory(request)
    return self.parse_trades(response)
'''
#
# ​   交易对 symbol
#
# ​   k线    1min  5min    30min   1h  4h     最多需要500 足够
#
# ​   时间周期        20条为一周期  10条为一周期
#
# ​   偏移量
#
# ​   哪种计算方法
#
# ​   使用哪个价格计算  close open