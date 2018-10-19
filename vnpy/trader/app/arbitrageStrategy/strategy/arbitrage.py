# encoding: UTF-8

"""
一个ATR-RSI指标结合的交易策略，适合用在股指的1分钟和5分钟线上。

注意事项：
1. 作者不对交易盈利做任何保证，策略代码仅供参考
2. 将IF0000_1min.csv用ctaHistoryData.py导入MongoDB后，直接运行本文件即可回测策略

"""

from vnpy.trader.vtObject import VtBarData
from vnpy.trader.vtConstant import EMPTY_STRING
from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate, 
                                                     BarGenerator, 
                                                     ArrayManager)
import threading


########################################################################
class Arbitrage(CtaTemplate):
    """结合ATR和RSI指标的一个分钟线交易策略"""
    className = u'跨交易所套利'
    author = u'八荒六合'

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(Arbitrage, self).__init__(ctaEngine, setting)
        self.p1Exchange = setting['p1Exchange']
        self.p2Exchange = setting['p2Exchange']
        self.p1Symbol = setting['p1Symbol']
        self.p2Symbol = setting['p2Symbol']
        self.spreadRatio = setting['spreadRatio']

        self.slippage = 0.000  # 设定市场价滑点百分比
        # 设定市场初始 ------------现在没有接口，人工转币，保持套利市场平衡--------------
        self.base_reserve = 0.0  # 设定账户最少预留数量,根据你自己的初始市场情况而定, 注意： 是数量而不是比例
        self.quote_reserve = 0.0

        self.p1OrderID = {}
        self.p2OrderID = {}
        self.netPos = 0
        self.p1Depth = {}
        self.p2Depth = {}
        self.lastExchange = ''
        self.filledOrders = []
        self.abtLock = threading.Lock()

    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略初始化' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略启动' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略停止' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        self.bg.updateTick(tick)

    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        pass

    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        # 更新净持仓数量
        self.writeCtaLog('onTrade: %s %s %s'%(exchange, symbol, order))
        if order['filled']==0:
            return
        self.filledOrders.append(order)
        if order['side'] == 'buy':
            self.netPos += order['filled']
        else:
            self.netPos -= order['filled']
        if abs(self.netPos)<=0.0001:
            self.netPos = 0
            self.p1OrderID = {}
            self.p2OrderID = {}
            buyTotal = 0
            sellTotal = 0
            for order in self.filledOrders:
                if order['side'] == 'buy':
                    buyTotal += order['cost']
                else:
                    sellTotal += order['cost']
            profit = sellTotal - buyTotal
            self.writeCtaLog('%s accomplished with profit: %f',symbol, profit)
            self.filledOrders = []
        else:
            self.hedge()

    #----------------------------------------------------------------------
    def onTrade(self, trade):
        # 发出状态更新事件
        self.putEvent()

    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass

    #寻找差价机会
    def arbitrage(self):
        try:
            self.abtLock.acquire()
            if not self.p1Depth or not self.p2Depth:
                self.abtLock.release()
                return
            p1Exchange = self.p1Depth[self.p1Symbol]['exchange']
            #p2Exchange = self.p2Depth[self.p2Symbol]['exchange']
            # 如果P1未成交，撤单
            if self.p1OrderID.get(p1Exchange):
                order = self.p1.fetchOrder(self.p1OrderID[p1Exchange]['id'], p1Exchange, self.p1Symbol)
                if order['status']=='open':
                    self.writeCtaLog('canceling p1 %s order %s %s', p1Exchange, self.p1OrderID[p1Exchange], order)
                    self.p1.cancelOrder(self.p1OrderID[p1Exchange], p1Exchange, self.p1Symbol)
                self.abtLock.release()
                return
            # 如果有净仓位则执行对冲
            if self.netPos:
                self.hedge()
                self.abtLock.release()
                return
            # 计算价差的bid/ask
            p1Bids = self.p1Depth[self.p1Symbol]['data']['bids']
            p2Bids = self.p2Depth[self.p2Symbol]['data']['bids']
            p1Asks = self.p1Depth[self.p1Symbol]['data']['asks']
            p2Asks = self.p2Depth[self.p2Symbol]['data']['asks']
            spreadBidPrice = p1Bids[0][0] - p2Asks[0][0]
            spreadAskPrice = p1Asks[0][0] - p2Bids[0][0]
            spreadBidVolume = min(p1Bids[0][1], p2Asks[0][1])
            spreadAskVolume = min(p1Asks[0][1], p2Bids[0][1])
            if spreadBidPrice > p1Bids[0][0]*self.spreadRatio:
                self.p1OrderID[p1Exchange] = self.p1.sell(self.p1Symbol, p1Bids[0][0], spreadBidVolume, p1Exchange)
                self.lastExchange = p1Exchange
                self.writeCtaLog('find sell %f spread: %f, vol: %f , in p1 %s Sell id: %s ',p1Bids[0][0], spreadBidPrice, spreadBidVolume,p1Exchange, self.p1OrderID[p1Exchange])
            elif spreadAskPrice < - p1Asks[0][0]*self.spreadRatio:
                self.p1OrderID[p1Exchange] = self.p1.buy(self.p1Symbol, p1Asks[0][0], spreadAskVolume, p1Exchange)
                self.lastExchange = p1Exchange
                self.writeCtaLog('find buy %f spread: %f, vol: %f , in p1 %s Buy id: %s ',p1Asks[0][0], spreadAskPrice, spreadAskVolume, p1Exchange, self.p1OrderID[p1Exchange])
            self.abtLock.release()
        except Exception as e:
            self.writeCtaLog('error in arbitrage: %s',e)
            self.abtLock.release()

    #在P2对冲
    def hedge(self):
        volume = abs(self.netPos)
        p2Exchange = self.p2Depth[self.p2Symbol]['exchange']
        depth = self.p2Depth[self.p2Symbol]['data']
        if not self.p2OrderID or not self.p2OrderID[p2Exchange]: self.p2OrderID[p2Exchange]=[]
        if self.netPos > 0:
            self.writeCtaLog('sell hedge in p2 %s: %s at price %f vol %f',p2Exchange,self.p2Symbol,depth['bids'][5][0],volume)
            self.p2OrderID[p2Exchange].append(self.p2.sell(self.p2Symbol,depth['bids'][5][0],volume,p2Exchange))
        elif self.netPos < 0:
            self.writeCtaLog('buy hedge in p2 %s: %s at price %f vol %f',p2Exchange,self.p2Symbol,depth['asks'][5][0],volume)
            self.p2OrderID[p2Exchange].append(self.p2.buy(self.p1Symbol,depth['asks'][5][0],volume,p2Exchange))