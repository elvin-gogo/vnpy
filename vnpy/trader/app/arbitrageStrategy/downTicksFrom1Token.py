# encoding: UTF-8
import requests
import json
import multiprocessing.dummy as thread
import gzip
from pymongo import MongoClient
import os
import time
import datetime
import math
from tqdm import tqdm
import utils.logger as logger

log = logger.getLog()

base = ['cmt','btc','eth','eos','ltc','kcash','xrp']
quote = ['eth','usd','usdt','btc']
exchange = ['binance','okex','huobip','bitmex','bitfinex']
symbolsRemain = []

url = 'http://alihz-net-0.qbtrade.org'
conn = MongoClient('18.179.204.45',23377)
db = conn.admin
db.authenticate('testCoin','testCoin123456')
db = conn.depth
downIndex = 0
dbIndex = 0

def downloadFile(url, filename):
    log.info('downloading file: %s'%filename)
    global downIndex
    downIndex+=1
    block_size = 1024
    r = requests.get(url, stream=True,headers={'Accept-Encoding': None})
    total_size = int(r.headers.get('content-length', 0))
    if total_size<block_size: return 0
    #print('file %s with size: %d', filename, total_size)
    wrote = 0
    progress = 0.1
    with open(filename, 'wb') as f:
        for data in tqdm(r.iter_content(block_size),desc='down:'+filename,total=math.ceil(total_size // block_size), unit='KB',
                         unit_scale=True,dynamic_ncols=True,position=downIndex):
            wrote = wrote + len(data)
            f.write(data)
            if wrote/total_size>progress:
                progress+=0.1
                log.info('downloading file %s progress %.f%%'%(filename,wrote/total_size*100))
    if total_size != 0 and wrote != total_size:
        log.error("ERROR, something went wrong, download again")
        return downloadFile(url, filename)
    return total_size

def storeDB(contract):
    start = time.time()
    filename = '%s.zip' % contract.replace('/', '-')
    log.info('%s decompressing and databasing....'%filename)
    before = time.time()
    col = db[contract]
    progress = 0.1
    global dbIndex
    dbIndex+=1
    with gzip.open(filename) as zip:
        lines = zip.readlines()
    stored = 0
    total = len(lines)
    pt = tqdm(desc='db:'+contract,total=total,position=dbIndex)
    for line in lines:
        j = json.loads(str(line.decode('utf-8')))
        j['_id']=j['exchange_time']
        col.save(j)
        stored += 1
        pt.update()
        if stored/len(lines)>progress:
            progress+=0.05
            log.info('storing %s progress %.f%%'%(filename,stored/total*100))
    log.info('decompressed and databased %s with %.2f seconds' % (filename, float(time.time() - before)))
    os.remove(filename)
    spent = time.time()-start
    log.info("%s处理完成，耗时%s秒"%(contract,str(spent)))
    log.info("symbols remaining: %s", symbolsRemain)

def downToDB(param):
    start = time.time()
    filename='%s.zip'%param['contract'].replace('/','-')
    log.info('downloading %s: '%filename)
    before = time.time()
    global symbolsRemain
    symbolsRemain.remove(param['contract'])
    total = downloadFile(url+'/hist-ticks?date=%s&contract=%s'%(param['date'],param['contract'])+'&format=json',filename)
    if total==0:
        log.info('%s has no data!'%filename)
        return
    log.info('downloaded %s with %.2s seconds'%(filename,float(time.time()-before)))
    p = thread.Process(target=storeDB,args=(param['contract'],))
    p.daemon=False
    p.start()
    spent = time.time() - start
    return spent

def getSymbol(allSymbol):
    ret = []
    for s in allSymbol:
        es = s.split('/')
        ss = es[1].split('.')
        #bitmex期货
        if len(ss)==3 and ss[2]!='td':
            continue
        hasBase = False
        hasQuote = False
        hasEx = False
        for bs in base:
            if bs == ss[0]:
                hasBase = True
        for qs in quote:
            if qs == ss[1]:
                hasQuote = True
        for ex in exchange:
            if ex == es[0]:
                hasEx = True
        if hasBase and hasQuote and hasEx:
            ret.append(s)
    return ret

if __name__ == '__main__':
    global symbolsRemain
    today=datetime.date.today()
    oneday=datetime.timedelta(days=1)
    yesterday=today
    for i in range(0,10):
        before = time.time()
        yesterday=yesterday-oneday
        log.info('downloading symbols:')
        response = requests.get(url+ '/contracts?date=%s&format=json'%yesterday)
        j = response.json()
        symbols = getSymbol(j)
        symbolsRemain = symbols.copy()
        log.info('total symbols: %d, matched symbols: %d'%(len(j),len(symbols)))
        for s in range(0,len(symbols)):
            symbols[s]={'contract':symbols[s],'date':str(yesterday)}
        downPool=thread.Pool(10)
        res = downPool.map(downToDB, symbols)
        log.info(res)
        log.info("日期%s所有数据处理完成，总耗时%.2f秒" % (yesterday, float(time.time()-before)))


