import sys
currentDir = os.getcwd()
sys.path.append(currentDir + '/Strategy')
from momentumTrading.MomentumState import MomentumState

class outOfMarket(PairsState):
	def __init__(self,name,edges,actions,finalStates, stateConstants, indicators):
		MomentumState.__init__(self,name,edges,actions,finalStates)
		self.stateConstants = stateConstants

	def enterMarket(self,timestamp, indicators, prices, toPass = None):
		if((indicators['PSAR_Indicator'] == 1) and (indicators['SMBA_Indicator'] == 1) and (indicators['OLS_Indicator'] == 1)):
			return True, {'Price': prices[prices.index == timestamp], 'Direction': 1}
		elif((indicators['PSAR_Indicator'] == -1) and (indicators['SMBA_Indicator'] == -1) and (indicators['OLS_Indicator'] == -1))
			return True, {'Price': prices[prices.index == timestamp], 'Direction': 1}
		else:
			return False, {}

	def preRequisites(self,prices, timestamp, toPass):
		row = self.indicators[self.indicators.index == timestamp]
		return row
