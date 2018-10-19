import pymongo
import arrow

if __name__ == '__main__':
    '''
    dbClient = pymongo.MongoClient('18.179.204.45',23377)
    dbClient['admin'].authenticate('testCoin','testCoin123456')
    db = dbClient['depth']
    cNames = db.collection_names()
    format = '%Y-%m-%dT%H:%M:%S.000000%z'
    for i in range(5, len(cNames)):
        collection = db[cNames[i]].find()
        for data in collection:
           if(type(data['_id'])==unicode):
               time = arrow.get(data['_id'])
               print(time.strftime(format))
    '''
    time1 = arrow.get(arrow.now().date().today())
    for i in range(10,0,-1):
        time2 = time1.shift(days=-1*i)
        print(str(time2.date()))
