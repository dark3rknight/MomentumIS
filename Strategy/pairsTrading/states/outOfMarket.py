import sys
sys.path.append('/home/ishan/Desktop/Ishan/Stock Data/Code Files/Strategy')
from pairsTrading.PairsState import PairsState

class outOfMarket(PairsState):
	def __init__(self, name,edges,actions,finalStates,stateConstants):
		PairsState.__init__(self,name,edges,actions,finalStates,stateConstants['colName'], stateConstants['offset'], stateConstants['momentumWindow'], stateConstants['pastWindow'])
		self.stateConstants = stateConstants

	def enterMarket(self,stock1dfs, stock2dfs, indicators,toPass = None):			
		datapoint, zscore, correlation, momentum, priceMomentum, zScores_30m, stock1_std, stock2_std, flag = indicators
		if(zscore > 0):
			if((zscore > self.stateConstants['zscoreBuy'])and((zscore < self.stateConstants['zscoreStopLoss']) or (not self.stateConstants['stopLossFlag'])) and ((correlation > self.stateConstants['correlationSelectionThreshold']) or (not self.stateConstants['correlationCheckFlag'])) and flag):
				PairsState.cPCount = 0
				PairsState.skipCounter = 0
				return True,[1, datapoint, zscore, correlation, momentum, priceMomentum, [stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]], [1/stock1_std, 1/stock2_std]]
			else:
				return False,[0, datapoint, zscore, correlation, momentum, priceMomentum,[stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]], [1/stock1_std, 1/stock2_std]]
		else:
			if((zscore < -self.stateConstants['zscoreBuy'])and((zscore > -self.stateConstants['zscoreStopLoss']) or (not self.stateConstants['stopLossFlag'])) and ((correlation > self.stateConstants['correlationSelectionThreshold']) or (not self.stateConstants['correlationCheckFlag'])) and flag):
				PairsState.cPCount = 0
				PairsState.skipCounter = 0
				return True,[-1, datapoint, zscore, correlation, momentum, priceMomentum,[stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]], [1/stock1_std, 1/stock2_std]]
			else:
				return False,[0, datapoint, zscore, correlation, momentum, priceMomentum,[stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]], [1/stock1_std, 1/stock2_std]]

	def preRequisites(self,stock1dfs, stock2dfs, toPass):
		datapoint, zscore, correlation, stock1_std, stock2_std, zScores_30m, flag  = self.calculateIndicators(stock1dfs, stock2dfs)
		momentum, priceMomentum = self.calculateMomentumIndicators(stock1dfs, stock2dfs,zscore, toPass[1])
		return datapoint,zscore,correlation, momentum, priceMomentum, zScores_30m, stock1_std, stock2_std, flag