# encoding: UTF-8

from .ctaEngine import CtaEngine
from .uiCtaWidget import CtaEngineManager

appName = 'CtaStrategy'
appDisplayName = u'套利策略'
appEngine = CtaEngine
appWidget = CtaEngineManager
appIco = 'cta.ico'