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
		MomentumState.__init__(self,name,edges,actions,finalStates,stateConstants['colName'], stateConstants['offset'], stateConstants['momentumWindow'], stateConstants['pastWindow'])
		self.stateConstants = stateConstants

	def exitMarket(self,timestamp, indicators, prices, toPass = None):
		if((indicators['PSAR_Indicator'] == 1) and (indicators['SMBA_Indicator'] == 1) and (indicators['OLS_Indicator'] == 1)):
			return True, {'Price': prices[prices.index == timestamp], 'Direction': 1}
		elif((indicators['PSAR_Indicator'] == -1) and (indicators['SMBA_Indicator'] == -1) and (indicators['OLS_Indicator'] == -1))
			return True, {'Price': prices[prices.index == timestamp], 'Direction': 1}
		else:
			return False, {}

	def stopLoss(self,timestamp, prices,toPass):
		datapoint, zscore, correlation, momentum, priceMomentum, zScores_30m, stock1_std, stock2_std = indicators
		if(toPass[0] == 1):
			if(zscore > self.stateConstants['zscoreStopLoss'])and(self.stateConstants['stopLossFlag']):
				return True,[-1, datapoint, zscore, correlation, momentum, priceMomentum, [stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]]]
			else:
				return False,[1, datapoint, zscore, correlation, momentum, priceMomentum, [stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]]]
		else:
			if(zscore < -self.stateConstants['zscoreStopLoss'])and(self.stateConstants['stopLossFlag']):
				return True,[-1, datapoint, zscore, correlation, momentum, priceMomentum, [stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]]]
			else:
				return False,[-1, datapoint, zscore, correlation, momentum, priceMomentum, [stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]]]

	def preRequisites(self,prices, timestamp, toPass):
		row = self.indicators[self.indicators.index == timestamp]
		return row
