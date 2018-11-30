# encoding: UTF-8

from __future__ import print_function

import json
import time
import datetime

import requests
from pymongo import MongoClient, ASCENDING

from vnpy.trader.vtObject import VtBarData
from vnpy.trader.app.ctaStrategy.ctaBase import MINUTE_DB_NAME
from multiprocessing.pool import Pool

# 加载配置
config = open('config.json')
setting = json.load(config)

MONGO_HOST = setting['MONGO_HOST']
MONGO_PORT = setting['MONGO_PORT']
SYMBOLS = setting['SYMBOLS']

mc = MongoClient(MONGO_HOST, MONGO_PORT)                        # Mongo连接
db = mc[MINUTE_DB_NAME]                                         # 数据库

def trans1TokenSymbol(symbol):
    exchange,tarSymbol = symbol.upper().split('/')
    tarSymbol=tarSymbol.split('.')
    return tarSymbol[0]+'/'+tarSymbol[1]+'.'+exchange

#----------------------------------------------------------------------
def generateVtBar(vtSymbol, d):
    """生成K线"""
    bar = VtBarData()
    symbol,exchange=vtSymbol.split('.')
    bar.symbol = symbol
    bar.exchange = exchange
    bar.vtSymbol = '.'.join([bar.symbol, bar.exchange])
    bar.datetime = datetime.datetime.fromtimestamp(d['timestamp'])
    bar.date = bar.datetime.strftime('%Y%m%d')
    bar.time = bar.datetime.strftime('%H:%M:%S')
    bar.open = d['open']
    bar.high = d['high']
    bar.low = d['low']
    bar.close = d['close']
    bar.volume = d['volume']
    
    return bar

#----------------------------------------------------------------------
def downMinuteBarBySymbol(symbol, period, start, end):
    """下载某一合约的分钟线数据"""
    startTime = time.time()
    vtSymbol = trans1TokenSymbol(symbol)
    cl = db[vtSymbol]
    cl.ensure_index([('datetime', ASCENDING)], unique=True)         
    
    startDt = datetime.datetime.strptime(start, '%Y%m%d')
    endDt = datetime.datetime.strptime(end, '%Y%m%d')
    
    url = 'https://1token.trade/api/v1/quote/candles'

    startTimeStamp = time.mktime(startDt.timetuple())
    endTimeStamp = time.mktime(endDt.timetuple())
    while startTimeStamp<endTimeStamp:
        params = {
            'contract': symbol,
            'since': startTimeStamp,
            'until': startTimeStamp+24*60*60,
            'duration': period
        }
        print(u'开始下载%s %s的数据'%(datetime.datetime.fromtimestamp(startTimeStamp).strftime('%Y-%m-%dT%H:%M:%S'),symbol))
        try:
            resp = requests.get(url, headers={}, params=params,timeout=10)
        except Exception as e:
            print(u'%s数据下载失败 %s ，重试' %(symbol,e))
            continue
        if resp.status_code != 200:
            print(u'%s数据下载失败，重试' %symbol)
            continue

        startTimeStamp+=24*60*60
        l = resp.json()

        print(u'%s %s数据存入数据库'%(datetime.datetime.fromtimestamp(startTimeStamp).strftime('%Y-%m-%dT%H:%M:%S'),symbol))
        for d in l:
            bar = generateVtBar(vtSymbol, d)
            d = bar.__dict__
            flt = {'datetime': bar.datetime}
            cl.replace_one(flt, d, True)
        print('存储完成')
    endTime = time.time()
    cost = (endTime - startTime) * 1000

    print(u'合约%s数据下载完成%s - %s，耗时%s毫秒' %(symbol, startDt, endDt, cost))


# ----------------------------------------------------------------------
def downTickerBySymbol(symbol,period,start,end):
    """下载某一合约的分钟线数据"""
    startTime=time.time()
    vtSymbol=trans1TokenSymbol(symbol)
    cl=db[vtSymbol]
    cl.ensure_index([('datetime',ASCENDING)],unique=True)

    startDt=datetime.datetime.strptime(start,'%Y%m%d')
    endDt=datetime.datetime.strptime(end,'%Y%m%d')

    url='http://alihz-net-0.qbtrade.org/hist-ticks'

    start=time.mktime(startDt.timetuple())
    end=time.mktime(endDt.timetuple())
    while start<end:
        params={
            'contract':symbol,
            'date':start,
            'format':'json'
        }
        print(u'开始下载%s %s的数据'%(datetime.datetime.fromtimestamp(start).strftime('%Y-%m-%dT%H:%M:%S'),symbol))
        resp=requests.get(url,headers={},params=params)

        if resp.status_code!=200:
            print(u'%s数据下载失败，重试'%symbol)
            continue

        start+=24*60*60
        l=resp.json()

        print(u'%s %s数据存入数据库'%(datetime.datetime.fromtimestamp(start).strftime('%Y-%m-%dT%H:%M:%S'),symbol))
        for d in l:
            bar=generateVtBar(vtSymbol,d)
            d=bar.__dict__
            flt={'datetime':bar.datetime}
            cl.replace_one(flt,d,True)
        print('存储完成')
    endTime=time.time()
    cost=(endTime-startTime)*1000

    print(u'合约%s数据下载完成%s - %s，耗时%s毫秒'%(symbol,l[0]['time'],l[-1]['time'],cost))

#----------------------------------------------------------------------
def downloadAllMinuteBar(start, end):
    """下载所有配置中的合约的分钟线数据"""
    print('-' * 50)
    print(u'开始下载合约分钟线数据')
    print('-' * 50)

    pool = Pool(len(SYMBOLS))
    for symbol in SYMBOLS:
        #pool.apply_async(downMinuteBarBySymbol,(symbol, '1min', start, end,))
        downMinuteBarBySymbol(symbol, '1min', start, end)
        time.sleep(10)

    print('-' * 50)
    print(u'合约分钟线数据下载完成')
    print('-' * 50)


    