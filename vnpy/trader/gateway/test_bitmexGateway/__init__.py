# encoding: UTF-8

from vnpy.trader import vtConstant
from .test_bitmexGateway import TestBitmexGateway

gatewayClass = TestBitmexGateway
gatewayName = 'TESTBITMEX'
gatewayDisplayName = 'TESTBITMEX'
gatewayType = vtConstant.GATEWAYTYPE_BTC
gatewayQryEnabled = False