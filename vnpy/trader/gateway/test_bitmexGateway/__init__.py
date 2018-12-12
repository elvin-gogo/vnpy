# encoding: UTF-8

from vnpy.trader import vtConstant
from .test_bitmexGateway import BitmexGateway

gatewayClass = BitmexGateway
gatewayName = 'test_BITMEX'
gatewayDisplayName = 'TESTBITMEX'
gatewayType = vtConstant.GATEWAYTYPE_BTC
gatewayQryEnabled = True