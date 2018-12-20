# -*- coding: utf-8 -*-

import os
import sys

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ex = ct.bitmex({
    'apiKey': 'oJMFY840ra5kjRPPTcoG0di3',
    'secret': 'aVFMzn3AvVcWKfsc0Wc6mmbf6cRuHHyevOqfOYxqJe9x9s7t',
    'enableRateLimit': True,
})

symbol = 'XBTU18'  # bitcoin contract according to bitmex futures coding
type = 'StopLimit'  # or 'market', or 'Stop' or 'StopLimit'
side = 'sell'  # or 'buy'
amount = 1
price = 6500.0  # or None

# extra params and overrides
params = {
    'stopPx': 6000.0,  # if needed
}
print(ex)

order = ex.create_order(symbol, type, side, amount, price, params)
print(order)
