# encoding: UTF-8

from datetime import datetime,timedelta
import arrow
from vnpy.trader.widget.uiKLine import *
from vnpy.trader.uiBackMainWindow import *

from vnpy.trader.vtFunction import *
import pymongo
########################################################################
from vnpy.trader.app.ctaStrategy.ctaBacktesting import BacktestingEngine, MINUTE_DB_NAME

class BackManager(QtWidgets.QMainWindow):
    signal = QtCore.Signal(type(Event()))

    def __init__(self, main,tradePath,optKType):
        super(BackManager, self).__init__()
        self.mainWindow = main
        self.stopOrderMonitor = None
        self.klineDay = None
        self.klineOpt = None

        self.dayBarData = {}
        self.hourBarData = {}
        self.daySarData={}
        self.hourSarData = {}
        self.hourListSig={}
        self.currrentSymbol = ""
        self.csvTradeData=self.loadcsvTradeData(tradePath)
        self.optKType=optKType
        self.initUi()
        self.symbolSelect()
        self.startTime = None
        self.endTime = None

    #----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        ##K线跟随
        for  opt in  self.optKType:
            if opt=="day":
                self.klineDay = KLineWidget(name="day")
                self.mainWindow.createDock(self.klineDay,'day', u"周线", QtCore.Qt.RightDockWidgetArea,True)
            else:
                self.klineOpt = KLineWidget(name="opt="+opt)
                self.mainWindow.createDock(self.klineOpt,'opt'+opt, u"操作周期线", QtCore.Qt.RightDockWidgetArea,True)

        #持仓量
        self.stopOrderMonitor = StopOrderMonitor()
        self.mainWindow.createDock(self.stopOrderMonitor, 'stopOrderMonitor', u"持仓量",QtCore.Qt.LeftDockWidgetArea, False)
        self.stopOrderMonitor.cellDoubleClicked.connect(self.symbolSelect)  # 注册signal
        self.stopOrderMonitor.setMaximumWidth(456)
        self.stopOrderMonitor.setMinimumWidth(456)
        self.updateMonitor()  ##更新一下数据

        self.mainWindow.saveWindowSettings('default')

    def setPath(self,path):
        self.filePath = path

    #################################################################################################################################
    def updateMonitor(self):
        varDict=[]
        ##更新合约
        tradeCount = self.csvTradeData.shape[0]
        curentIndex = 1
        while curentIndex<tradeCount:
            varSymbol=VtOrderData()
            varSymbol.symbol=self.csvTradeData.ix[[curentIndex]].values[0][3]  ##合约
            varSymbol.orderTime= self.csvTradeData.ix[[curentIndex]].values[0][0]  ##时间
            varSymbol.direction=self.csvTradeData.ix[[curentIndex]].values[0][7]
            varSymbol.offset=self.csvTradeData.ix[[curentIndex]].values[0][8]
            varSymbol.price=self.csvTradeData.ix[[curentIndex]].values[0][9]
            varSymbol.volume=self.csvTradeData.ix[[curentIndex]].values[0][10]
            if type(varSymbol.symbol) == float:#排除空数据
                curentIndex += 1
                continue

            varDict.append(varSymbol)
            curentIndex += 1
        self.startTime = datetime.strptime(self.csvTradeData.ix[1].values[0],'%Y-%m-%d %H:%M:%S')
        self.endTime = datetime.strptime(self.csvTradeData.ix[tradeCount].values[0],'%Y-%m-%d %H:%M:%S')
        self.stopOrderMonitor.updateAllData(varDict)
    #---------------------------------------------------------------------------
        ##显示合约k线

    def symbolSelect(self, row=None, column=None):
        if  row==None:
            row=0

        symbol = str(self.stopOrderMonitor.item(row, 0).text())
        print (symbol)
        if symbol:
            self.loadKlineData(symbol)

    def loadKlineData(self, symbol):
        if self.currrentSymbol == symbol:
            return
        self.currrentSymbol = symbol
        self.loadBar(symbol)
        self.loadSig(symbol)

        # 插入bar数据
        for opt in self.optKType:
            if opt=="day":
                self.klineDay.KLtitle.setText(symbol + "opt=day", size='10pt')
                self.klineDay.loadDataBar(self.dayBarData[symbol])
            else:
                self.klineOpt.KLtitle.setText(symbol + " opt="+opt, size='10pt')
                self.klineOpt.loadDataBar(self.hourBarData[symbol])
        self.klineOpt.updateSig(self.hourListSig[symbol])

    ############################################################################
    # 加载kline数据
    def loadBar(self, symbol):
        for opt in self.optKType:
            if opt=="day":
                if not self.dayBarData.has_key(symbol):
                   dbDayList = self.loadAllBarFromDb('day', symbol)
                   self.dayBarData[symbol] = dbDayList
            else:
                if not self.hourBarData.has_key(symbol):
                    dbHourList = self.loadAllBarFromDb(MINUTE_DB_NAME, symbol)
                    self.hourBarData[symbol] = dbHourList


    def loadSig(self, symbol):
        txtData = self.hourBarData[symbol]
        count = self.hourBarData[symbol].shape[0]
        tradeCount = self.csvTradeData.shape[0]
        tradeIndex = 1
        listSig = [None]*count
        for sigIndex in range(0,count):
            kTime = arrow.get(str(txtData.ix[[sigIndex]].values[0][3]))
            #kTimeNext = arrow.get(str(txtData.ix[[sigIndex + 1]].values[0][3]))
            tradeTime = arrow.get(str(self.csvTradeData.ix[[tradeIndex]].values[0][0]))
            if kTime.timestamp>tradeTime.timestamp:
                sigData={"direction":self.csvTradeData.ix[[tradeIndex]].values[0][7],
                          "offset":self.csvTradeData.ix[[tradeIndex]].values[0][8],
                          "price":self.csvTradeData.ix[[tradeIndex]].values[0][9]}
                listSig[sigIndex]=sigData
                tradeIndex+=1
        self.hourListSig[symbol] = listSig

    # ----------------------------------------------------------------------
    def loadAllBarFromDb(self, dbName, collectionName):
        dbClient=pymongo.MongoClient(globalSetting['mongoHost'],globalSetting['mongoPort'])
        collection=dbClient[dbName][collectionName]
        flt={'datetime':{'$gte':self.startTime,'$lt':self.endTime}}
        data=pd.DataFrame(list(collection.find(flt).sort('datetime')))
        return data

    def loadcsvTradeData(self,tradePath):
       if  tradePath:
            # fieldnames = ['dt', 'symbol', 'exchange', 'vtSymbol', 'tradeID', 'vtTradeID', 'orderID', 'vtOrderID',
            #               'direction', 'offset', 'price', 'volume', 'tradeTime', "gatewayName", "rawData"]
            if os.path.exists(tradePath):
                return pd.DataFrame.from_csv(tradePath, encoding="utf_8_sig", index_col=7)
       return None
    #----------------------------------------------------------------------
    def createDock(self, widget, widgetName, widgetArea):
        """创建停靠组件"""
        dock = QtWidgets.QDockWidget(widgetName)
        dock.setWidget(widget)
        dock.setObjectName(widgetName)
        dock.setFeatures(dock.DockWidgetFloatable|dock.DockWidgetMovable)
        self.addDockWidget(widgetArea, dock)
        return widget, dock
#############################################################################

class StopOrderMonitor(BasicMonitor):
    """日志监控"""
    #----------------------------------------------------------------------
    def __init__(self, parent=None):
        """Constructor"""
        super(StopOrderMonitor, self).__init__( parent)

        d = OrderedDict()
        d['symbol'] = {'chinese': u"合约", 'cellType':BasicCell}
        d['orderTime'] = {'chinese': u"时间", 'cellType':BasicCell}
        d['direction'] = {'chinese':u"direction", 'cellType':BasicCell}
        d['offset'] = {'chinese':u"offset", 'cellType':BasicCell}
        d['price'] = {'chinese':u"price", 'cellType':BasicCell}
        d['volume'] = {'chinese':u"volume", 'cellType':BasicCell}

        self.setHeaderDict(d)
        self.setFont(BASIC_FONT)
        self.initTable()

