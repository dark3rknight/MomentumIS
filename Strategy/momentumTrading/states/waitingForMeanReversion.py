import sys
sys.path.append('/home/ishan/Desktop/Ishan/Stock Data/Code Files/Strategy')
from pairsTrading.PairsState import PairsState
import numpy as np
import pandas as pd
import math

class waitingForMeanReversion(PairsState):
	def __init__(self,name,edges,actions,finalStates, stateConstants):
		PairsState.__init__(self,name,edges,actions,finalStates,stateConstants['colName'], stateConstants['offset'], stateConstants['momentumWindow'], stateConstants['pastWindow'])
		self.stateConstants = stateConstants

	def stopLoss(self,stock1dfs, stock2dfs,indicators, toPass):
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

	def meanRevertedandFiredOtherSide(self,stock1dfs, stock2dfs,indicators, toPass):
		datapoint, zscore, correlation, momentum, priceMomentum, zScores_30m, stock1_std, stock2_std = indicators
		if(toPass[0] == 1):
			if((zscore < -self.stateConstants['zscoreBuy'])and((zscore > -self.stateConstants['zscoreStopLoss']) or (not self.stateConstants['stopLossFlag'])) and ((correlation > self.stateConstants['correlationSelectionThreshold']) or (not self.stateConstants['correlationCheckFlag']))):
				return True,[-1, datapoint, zscore, correlation, momentum, priceMomentum, [stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]], [1/stock1_std, 1/stock2_std]]
			else:
				return False,[-1, datapoint, zscore, correlation, momentum, priceMomentum, [stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]], [1/stock1_std, 1/stock2_std]]
		else:
			if((zscore > self.stateConstants['zscoreBuy'])and((zscore < self.stateConstants['zscoreStopLoss']) or (not self.stateConstants['stopLossFlag'])) and ((correlation > self.stateConstants['correlationSelectionThreshold']) or (not self.stateConstants['correlationCheckFlag']))):
				return True,[1, datapoint, zscore, correlation, momentum, priceMomentum, [stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]], [1/stock1_std, 1/stock2_std]]
			else:
				return False,[1, datapoint, zscore, correlation, momentum, priceMomentum, [stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]], [1/stock1_std, 1/stock2_std]]

	def meanReverted(self,stock1dfs, stock2dfs,indicators, toPass):
		datapoint, zscore, correlation, momentum, priceMomentum, zScores_30m, stock1_std, stock2_std = indicators
		if(toPass[0] == 1):
			if(zscore < self.stateConstants['zscoreSell']):
				return True,[0, datapoint, zscore, correlation, momentum, priceMomentum, [stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]]]
			else:
				return False,[1, datapoint, zscore, correlation, momentum, priceMomentum, [stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]]]
		else:
			if(zscore > -self.stateConstants['zscoreSell']):
				return True,[0, datapoint, zscore, correlation, momentum, priceMomentum, [stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]]]
			else:
				return False,[-1, datapoint, zscore, correlation, momentum, priceMomentum, [stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]]]

	def stockHasMissingData(self,stock1dfs, stock2dfs,indicators,toPass):
		datapoint, zscore, correlation, momentum, priceMomentum, zScores_30m, stock1_std, stock2_std = indicators
		currentTime = stock1dfs[0].iloc[-1].DATE
		try:
			prevTime = stock1dfs[0].iloc[-2].DATE
			if(currentTime - prevTime > pd.Timedelta(days = 10)):
				return True,[toPass[0], datapoint, zscore, correlation, momentum, priceMomentum, [stock1dfs[0].iloc[-2][self.stateConstants['colName']],stock2dfs[0].iloc[-2][self.stateConstants['colName']]]]
			else:
				return False,[toPass[0], datapoint, zscore, correlation, momentum, priceMomentum, [stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]]]
		except IndexError:
			return False,[toPass[0], datapoint, zscore, correlation, momentum, priceMomentum, [stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]]]

	def tradeNotProfitable(self,stock1dfs, stock2dfs,indicators,toPass):
		datapoint, zscore, correlation, momentum, priceMomentum, zScores_30m, stock1_std, stock2_std = indicators
		if(not self.stateConstants['usePredictiveModel']):
			return False, [toPass[0], datapoint,zscore,correlation,momentum,priceMomentum, [stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]]]			
		try:
			stock1_inTradeData,stock2_inTradeData, entryTime, entryPos = self.get30mCandlesFromEntryPoint(stock1dfs, stock2dfs,toPass[1])
		except KeyError:
			return (False and self.stateConstants['usePredictiveModel']), [toPass[0], datapoint, zscore, correlation, momentum, priceMomentum, [stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]]]
		except IndexError:
			return (False and self.stateConstants['usePredictiveModel']), [toPass[0], datapoint, zscore, correlation, momentum, priceMomentum, [stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]]]
		if((not self.stateConstants['usePredictiveModelAtEveryIteration']) and (((len(stock1_inTradeData) - entryPos) < self.stateConstants['checkPoint'])or((len(stock1_inTradeData) - entryPos) > self.stateConstants['checkPoint'] + 11))):
			return False, [toPass[0], datapoint,zscore,correlation,momentum,priceMomentum, [stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]]]
		else:
			stock1_30mCandles, stock2_30mCandles = self.get30mCandlesForTheDay(stock1dfs,stock2dfs)
			cPCount = PairsState.cPCount - len(stock1_30mCandles)
			cPRange = np.arange(cPCount + 1, cPCount + len(stock1_30mCandles) + 1, 1)

			if(len(cPRange) != 0):
				variables = self.getVariables(stock1_inTradeData, stock2_inTradeData, cPRange, entryTime, entryPos, toPass[0])
				model = self.stateConstants['predictiveModel']
				flag = True
				try:
					result = model.predict_proba(variables)
				except:
					prediction = False
					flag = False

				if(flag):
					for i in range(len(result)):
						if(PairsState.skipCounter != self.stateConstants['predictiveModelCheckFrequency']):
							PairsState.skipCounter += 1
							return False, [toPass[0], datapoint,zscore,correlation,momentum,priceMomentum, [stock1dfs[0].iloc[-1][self.stateConstants['colName']], stock2dfs[0].iloc[-1][self.stateConstants['colName']]]]			
						PairsState.skipCounter = 0
						cutOff = self.getWeight(self.stateConstants['predictiveModelThreshold_startX'], self.stateConstants['predictiveModelThreshold_endX'], self.stateConstants['predictiveModelThreshold_startY'], self.stateConstants['predictiveModelThreshold_endY'], cPRange[i])
						if(result[i][0] >= cutOff):
							prediction = True
						else:
							prediction = False
						if(prediction == True):
							prices = [stock1_inTradeData.iloc[entryPos + cPRange[i]][self.colName],stock2_inTradeData.iloc[entryPos + cPRange[i]][self.colName]]
							time = [stock1_inTradeData.iloc[entryPos + cPRange[i]]['TIME'],stock2_inTradeData.iloc[entryPos + cPRange[i]]['TIME']]
							return (prediction and self.stateConstants['usePredictiveModel']), [toPass[0], datapoint, zscore, correlation, momentum, priceMomentum, prices,time]
						else:
							prices = [stock1dfs[0].iloc[-2][self.stateConstants['colName']],stock2dfs[0].iloc[-2][self.stateConstants['colName']]]
							time = [stock1dfs[0].iloc[-2]['TIME'],stock2dfs[0].iloc[-2]['TIME']]
							continue
				else:
					prices = [stock1dfs[0].iloc[-2][self.stateConstants['colName']],stock2dfs[0].iloc[-2][self.stateConstants['colName']]]
					time = [stock1dfs[0].iloc[-2]['TIME'],stock2dfs[0].iloc[-2]['TIME']]
			else:
				prices = [stock1dfs[0].iloc[-2][self.stateConstants['colName']],stock2dfs[0].iloc[-2][self.stateConstants['colName']]]
				time = [stock1dfs[0].iloc[-2]['TIME'],stock2dfs[0].iloc[-2]['TIME']]
				prediction = False
			return (prediction and self.stateConstants['usePredictiveModel']), [toPass[0], datapoint, zscore, correlation, momentum, priceMomentum, prices,time]

	def preRequisites(self,stock1dfs, stock2dfs, toPass):
		datapoint, zscore, correlation,stock1_std, stock2_std, zScores_30m, flag = self.calculateIndicators(stock1dfs, stock2dfs)
		momentum, priceMomentum = self.calculateMomentumIndicators(stock1dfs, stock2dfs, zscore, toPass[1])
		stock1_30mCandles, stock2_30mCandles = self.get30mCandlesForTheDay(stock1dfs,stock2dfs)
		PairsState.cPCount += len(stock1_30mCandles)
		return datapoint,zscore,correlation, momentum, priceMomentum, zScores_30m, stock1_std, stock2_std

	def collectDataForPrediction(self,stock1dfs, stock2dfs,toPass):
		try:
			stock1_inTradeData,stock2_inTradeData, entryTime, entryPos = self.get30mCandlesFromEntryPoint(stock1dfs, stock2dfs,toPass[1])
		except KeyError:
			return None
		except IndexError:
			return None
		cPRange = []
		rows = {}
		for cP in self.stateConstants['checkPointRange']:
			if((len(stock1_inTradeData) - entryPos) <= cP):
				break
			else:
				cPRange.append(cP)
		if(len(cPRange) == 0):
			return rows
		variables = self.getVariables(stock1_inTradeData, stock2_inTradeData, cPRange, entryTime, entryPos, toPass[0], typeList = True)
		counter = 0
		for cP in cPRange:
			rows[cP] = variables[counter]
			counter += 1
		return rows

	def getWeight(self,startX, endX, startY, endY, x):
	    x_new = ((x - startX)/(endX - startX))*8 - 4
	    return startY + self.sigmoid(x_new)*(endY - startY)

	def sigmoid(self,x):
	  return 1 / (1 + math.exp(-x))