import sys
import os
currentDir = os.getcwd()
sys.path.append(currentDir + '/Strategy')
from momentumTrading.MomentumState import MomentumState
import numpy as np
import pandas as pd
import math

class inMarket(MomentumState):
	def __init__(self,name,edges,actions,finalStates, stateConstants, indicators):
		MomentumState.__init__(self,name,edges,actions,finalStates,stateConstants['PriceColumn'])
		self.stateConstants = stateConstants
		self.indicators = indicators

	def exitMarket(self,timestamp, indicators, prices, toPass = None):
		if((indicators.ix[0]['PSAR_Indicator'] in [toPass['Direction'],0]) and (indicators.ix[0]['SMBA_Indicator'] in [toPass['Direction'],0]) and (indicators.ix[0]['OLS_Indicator'] in [toPass['Direction'],0])):
			return False, {'Price': prices[prices.index == timestamp], 'Direction': 1}
		else:
			return True, {'Price': prices['CLOSE'], 'Direction':0}

	def stopLoss(self,timestamp, indicators, prices, toPass = None):
		checkingPrice = float(prices.ix[0]['LOW'] if (toPass['Direction'] == 1) else prices.ix[0]['HIGH'])
		if(float(toPass['Direction']*toPass['stopLossLimit']) > float(toPass['Direction']*checkingPrice)):
			return True, {'Price': checkingPrice, 'Direction': 0}
		else:
			return False, {}

	def psarExit(self,timestamp, indicators, prices, toPass = None):
		pos = self.indicators.index.get_loc(timestamp)
		indicatorsPast = self.indicators.ix[pos - 1]
		if(toPass['Direction']*indicatorsPast['PSAR_Val'] > toPass['Direction']*(prices.ix[0]['LOW'] if toPass['Direction'] == 1 else prices.ix[0]['HIGH'])):
			return True, {'Price': indicatorsPast.ix[0]['PSAR_Val'], 'Direction': 0}
		else:
			return False,{}