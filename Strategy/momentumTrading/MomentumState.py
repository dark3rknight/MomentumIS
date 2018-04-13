import sys
import os
currentDir = os.getcwd()
sys.path.append(currentDir + '/Strategy')
from State import State
import pandas as pd
import scipy.stats as stats
import numpy as np
from datetime import timedelta, datetime
import pickle

class MomentumState(State):

	def __init__(self,name,edges,actions,finalStates, colName):
		State.__init__(self,name,edges,actions, finalStates, colName)

	def getVariables(self,stock1_inTradeData, stock2_inTradeData, checkPoints, entryTime, tradeEntry, direction, typeList = None):
		offset = max(self.stateConstants['momentumWindow_30m'], self.stateConstants['pastWindow_30m'])
		momentum = []
		priceMomentum = []
		correlations = []
		zScores = []
		datapoints = []
		profits = []
		for i in range(tradeEntry, tradeEntry + checkPoints[-1] + 1):
			mean, standardDeviation = self.createDistribution(list(stock1_inTradeData.iloc[i - offset: i][self.colName]),list(stock2_inTradeData.iloc[i - offset: i][self.colName]))
			datapoint = stock1_inTradeData.iloc[i][self.colName]/stock2_inTradeData.iloc[i][self.colName]
			datapoints.append(datapoint)
			zScore = self.calculateZScore(datapoint, mean, standardDeviation)
			zScores.append(zScore)
			correlations.append(stats.pearsonr(list(stock1_inTradeData.iloc[i - offset: i+1][self.colName]),list(stock2_inTradeData.iloc[i - offset: i+1][self.colName]))[0])

		for i in zScores:
			momentum.append((i - zScores[0])/abs(zScores[0]))

		for i in datapoints:
			priceMomentum.append((i - datapoints[0])/abs(datapoints[0]))

		entryPrice1 = stock1_inTradeData.iloc[tradeEntry][self.colName]
		entryPrice2 = stock2_inTradeData.iloc[tradeEntry][self.colName]
		data1 = list(stock1_inTradeData.iloc[tradeEntry:tradeEntry + checkPoints[-1] + 1][self.colName])
		data2 = list(stock2_inTradeData.iloc[tradeEntry:tradeEntry + checkPoints[-1] + 1][self.colName])
		for ind in range(len(data1)):
			profit1 = direction*100*((entryPrice1 - data1[ind])/entryPrice1)
			profit2 = -direction*100*((entryPrice2 - data2[ind])/entryPrice2)
			profits.append((profit1 + profit2)/2 - 0.1)

		if(direction == -1):
			momentum = -np.array(momentum)
			zScores = -np.array(zScores)
			priceMomentum = -np.array(priceMomentum)

		df = pd.DataFrame(columns = ['meanMomentum','minMomentum','maxMomentum','currentMomentum','meanPriceMomentum','minPriceMomentum','maxPriceMomentum','currentPriceMomentum','meanCorrelation','minCorrelation','maxCorrelation','currentCorrelation','meanProfit','minProfit','maxProfit','currentProfit', 'meanZscore','maxZscore','minZscore','currentZscore', 'timePassed','profitByTime'])
		rC = 0
		rows = []
		for cP in checkPoints:
			# print(len(momentum), len(priceMomentum), len(correlations), len(zScores), len(profits), cP)
			row = [np.mean(momentum[:cP]), np.min(momentum[:cP]), np.max(momentum[:cP]), momentum[cP],np.mean(priceMomentum[:cP]), np.min(priceMomentum[:cP]), np.max(priceMomentum[:cP]), priceMomentum[cP],np.mean(correlations[:cP]), np.min(correlations[:cP]), np.max(correlations[:cP]), correlations[cP],np.mean(profits[:cP]), np.min(profits[:cP]), np.max(profits[:cP]), profits[cP],np.mean(zScores[:cP]), np.min(zScores[:cP]), np.max(zScores[:cP]), zScores[cP], cP, (profits[cP]/float(cP))]
			df.loc[rC] = row
			rows.append(row)
			rC += 1
		if(typeList):
			return rows
		return df

	def preRequisites(self, timestamp, prices, toPass):
		row = self.indicators[self.indicators.index == timestamp]
		return row

	def getNextResult(self,prices, timestamp,toPass = None):
		selectedEdge = 'default'
		row = None
		indicators = self.preRequisites(timestamp,prices,toPass)
		result = None
		for edge in self.edges:
			if(edge == 'default'):
				continue
			else:
				flag, data = eval('self.' + edge + '(timestamp, indicators, prices,toPass)')
				if(flag):
					if(self.actions[edge] == 'exitMarket'):
						if(self.stateConstants['collectRegressionData']):
							row = self.collectDataForPrediction(stock1dfs, stock2dfs, toPass)
						else:
							row = None
					selectedEdge = edge
					break
				else:
					data = {}
		return selectedEdge, self.actions[selectedEdge], self.finalStates[selectedEdge],data, row