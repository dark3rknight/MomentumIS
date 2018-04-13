import sys
import os
currentDir = os.getcwd()
sys.path.append(currentDir + '/Strategy')
from momentumTrading.MomentumState import MomentumState

class outOfMarket(MomentumState):
	def __init__(self,name,edges,actions,finalStates, stateConstants, indicators):
		MomentumState.__init__(self,name,edges,actions,finalStates,stateConstants['PriceColumn'])
		self.stateConstants = stateConstants
		self.indicators = indicators

	def enterMarket(self,timestamp, indicators, prices, toPass = None):
		if((indicators.ix[0]['PSAR_Indicator'] == 1) and (indicators.ix[0]['SMBA_Indicator'] == 1) and (indicators.ix[0]['OLS_Indicator'] == 1)):
			return True, {'Price': prices['CLOSE'], 'Direction': 1}
		elif((indicators.ix[0]['PSAR_Indicator'] == -1) and (indicators.ix[0]['SMBA_Indicator'] == -1) and (indicators.ix[0]['OLS_Indicator'] == -1)):
			return True, {'Price': prices['CLOSE'], 'Direction': 1}
		else:
			return False, {}