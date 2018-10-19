# coding=utf-8
import requests
import json
import multiprocessing.dummy as thread
import gzip
from pymongo import MongoClient
import os
import time
import math
from tqdm import tqdm
import utils.logger as logger
import arrow
from settings import settings

log = logger.getLog()

base = ['cmt','btc','eth','eos','ltc','kcash','xrp']
quote = ['eth','usd','usdt','btc']
exchange = ['binance','okex','huobip','bitmex','bitfinex']

url = 'http://alihz-net-0.qbtrade.org'
dbClient = MongoClient(settings['mongoHost'],settings['mongoPort'])
if settings.get("mongoAuth"):
    dbClient['admin'].authenticate(settings['mongoAuth']['authName'],settings['mongoAuth']['authPass'])
db =dbClient['depth']
downIndex = 0
dbIndex = 0

def downloadFile(url, filename):
    global downIndex
    downIndex+=1
    log.info('downloading url: %s, index: %d' % (url,downIndex))
    try:
        block_size = 1024
        for i in range(0,10):
            r = requests.get(url, stream=True, headers={'Accept-Encoding': None})
            if r.status_code == 200:
                break
            log.error('%s response error %s, waiting for try again...'%(url,r.status_code))
            time.sleep(30)
        total_size = int(r.headers.get('content-length', 0))
        if total_size<block_size:
            return 0
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
    except Exception as e:
        log.error('exception in downloadFile: %s',e)

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
        exTime = j.get('exchange_time')
        if exTime == None:
            exTime = j.get('time')
            if exTime == None:
                log.error('error data: %s', j)
                continue
            else:
                j['exchange_time'] = exTime
        exTime = arrow.get(exTime)
        j['_id']=exTime.timestamp
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

def downToDB(param):
    start = time.time()
    filename='%s.zip'%param['contract'].replace('/','-')
    log.info('downloading %s: '%filename)
    before = time.time()
    total = downloadFile(url+'/hist-ticks?date=%s&contract=%s'%(param['date'],param['contract'])+'&format=json',filename)
    if total==0:
        log.info('%s has no data!'%(url+'/hist-ticks?date=%s&contract=%s'%(param['date'],param['contract'])+'&format=json'))
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
    today=arrow.get(arrow.now().date().today())
    for i in range(10,0,-1):
        before = time.time()
        yesterday=str(today.shift(days=-1*i).date())
        log.info('downloading symbols:')
        response = requests.get(url+ '/contracts?date=%s&format=json'%yesterday)
        j = response.json()
        symbols = getSymbol(j)
        log.info('total symbols: %d, matched symbols: %d'%(len(j),len(symbols)))
        for s in range(0,len(symbols)):
            symbols[s]={'contract':symbols[s],'date':str(yesterday)}
        #最大只能同时请求4个
        downPool=thread.Pool(4)
        res = downPool.map(downToDB, symbols)
        log.info(res)
        log.info("日期%s所有数据处理完成，总耗时%.2f秒" % (yesterday, float(time.time()-before)))

