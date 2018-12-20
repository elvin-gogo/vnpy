# -*- coding: utf-8 -*-
# Author: kai.zhang01
# Date: 2018/9/22 
# Desc:  获取对象



def Instance(exchange):

    od = __import__(exchange)
    obj = getattr(od, exchange)()
    return obj


if __name__ == '__main__':
    c = Instance('bitmex')
    print(c.fetch_orders("XBT/USD"))
    # print(c.fetch_orders('XBTU18'))
