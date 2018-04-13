import sys
import os
currentDir = os.getcwd()
sys.path.append(currentDir + '/Strategy')
from momentumTrading.MomentumState import MomentumState

class outOfMarket_lock(MomentumState):
	def __init__(self,name,edges,actions,finalStates, stateConstants, indicators):
		MomentumState.__init__(self,name,edges,actions,finalStates,stateConstants['PriceColumn'])
		self.stateConstants = stateConstants
		self.indicators = indicators

	def breakLock(self,timestamp, indicators, prices, toPass = None):
		if((indicators.ix[0]['PSAR_Indicator'] in [toPass['Direction'],0]) and (indicators.ix[0]['SMBA_Indicator'] in [toPass['Direction'],0]) and (indicators.ix[0]['OLS_Indicator'] in [toPass['Direction'],0])):
			return False, {'Price': prices[prices.index == timestamp], 'Direction': 1}
		else:
			return True, {'Price': prices.ix[0]['CLOSE'], 'Direction':0}

	def breakLockAndEnter(self,timestamp, indicators, prices, toPass = None):
		if((indicators.ix[0]['PSAR_Indicator'] in [toPass['Direction'],0]) and (indicators.ix[0]['SMBA_Indicator'] in [toPass['Direction'],0]) and (indicators.ix[0]['OLS_Indicator'] in [toPass['Direction'],0])):
			return False, {'Price': prices[prices.index == timestamp], 'Direction': 1}
		elif((indicators.ix[0]['PSAR_Indicator'] == -toPass['Direction']) and (indicators.ix[0]['SMBA_Indicator'] == -toPass['Direction']) and (indicators.ix[0]['OLS_Indicator'] == -toPass['Direction'])):
			return True, {'Price': prices.ix[0]['CLOSE'], 'EntryPrice': prices.ix[0]['CLOSE'], 'Direction': -toPass['Direction']}
		else:
			return False, {'Price': prices[prices.index == timestamp], 'Direction': 1}