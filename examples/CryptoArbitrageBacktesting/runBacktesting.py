# encoding: UTF-8

"""
展示如何执行策略回测。
"""

from __future__ import division


from vnpy.trader.app.arbitrageStrategy.arbitrageBacktesting import BacktestingEngine, MINUTE_DB_NAME


if __name__ == '__main__':
    from vnpy.trader.app.arbitrageStrategy.strategy.strategyKingKeltner import KkStrategy
    
    # 创建回测引擎
    engine = BacktestingEngine()
    
    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.TICK_MODE)

    # 设置回测用的数据起始日期
    engine.setStartDate('20120101')
    
    # 设置产品相关参数
    #engine.setSlippage(0.2)     # 不设置滑点
    engine.setRate(1/1000)      # 千1
    engine.setSize(1)           # 合约大小

    # 设置使用的历史数据库
    symbols = ['binance/btc.usdt','huobip/btc.usdt','okex/btc.usdt']
    engine.setDatabase(MINUTE_DB_NAME, symbols)
    
    # 在引擎中创建策略对象
    d = {}
    engine.initStrategy(KkStrategy, d)
    
    # 开始跑回测
    engine.runBacktesting()
    
    # 显示回测结果
    engine.showBacktestingResult()