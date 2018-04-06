import sys
sys.path.append('/home/ishan/Desktop/Ishan/Stock Data/Code Files/Strategy')
sys.path.append('/home/ishan/Desktop/Ishan/Stock Data/Code Files')
from State import State
import pandas as pd
import scipy.stats as stats
import numpy as np
from datetime import timedelta, datetime
import pickle

class PairsState(State):
	cPCount = 0
	skipCounter = 0
	def __init__(self,name,edges,actions,finalStates, colName, offset, momentumWindow, pastWindow):
		State.__init__(self,name,edges,actions, finalStates, colName)
		self.colName = colName
		self.offset = offset
		self.pastWindow = pastWindow
		self.momentumWindow = momentumWindow

	def calculateZScore(self,datapoint,mean,std):
		return (datapoint - mean)/std

	def createDistribution(self,stock1,stock2):
		data = [stock1[i]/stock2[i] for i in range(len(stock1))]
		return np.mean(data), np.std(data)

	def calculateIndicators(self, stock1dfs, stock2dfs):
		stock1df = stock1dfs[0]
		stock2df = stock2dfs[0]
		stock1df_30m, stock2df_30m = self.get30mCandlesForTheDay(stock1dfs, stock2dfs)
		stock1Price = stock1df.iloc[-1][self.colName]
		stock2Price = stock2df.iloc[-1][self.colName]
		pastData_stock1 = stock1df.iloc[-self.pastWindow - 1:-1][self.colName]
		pastData_stock2 = stock2df.iloc[-self.pastWindow - 1:-1][self.colName]
		pastData_stock1df = stock1df.iloc[-self.pastWindow - 1:-1]['DATE']
		prevDate = None
		flag = True
		for row in pastData_stock1df:
			date = row
			if(prevDate is not None):
				if(date - prevDate > pd.Timedelta(days = 10)):
					flag = False
					print(date,prevDate)
					break
			prevDate = date
		datapoint = stock1Price/stock2Price
		pastData_stock1_std = stock1df.iloc[-self.stateConstants['pastWindow_std'] - 1:-1][self.colName]
		pastData_stock2_std = stock2df.iloc[-self.stateConstants['pastWindow_std'] - 1:-1][self.colName]
		mean, standardDeviation = self.createDistribution(pastData_stock1, pastData_stock2)
		zscore = self.calculateZScore(datapoint,mean,standardDeviation)
		correlation = stats.pearsonr(pastData_stock1, pastData_stock2)[0]
		toReturn = [datapoint, zscore, correlation, np.std(pastData_stock1_std), np.std(pastData_stock2_std)]

		zScores_30m = []
		for i in range(stock1df_30m.shape[0]):
			stock1Price = stock1df_30m.iloc[i][self.colName]
			stock2Price = stock2df_30m.iloc[i][self.colName]
			datapoint = stock1Price/stock2Price
			zscore = self.calculateZScore(datapoint,mean,standardDeviation)
			zScores_30m.append([stock1Price, stock2Price, zscore])

		toReturn.append(zScores_30m)
		toReturn.append(flag)
		return toReturn

	def calculateMomentumIndicators(self,stock1dfs, stock2dfs,zscore, start = None):
		stock1df = stock1dfs[0]
		stock2df = stock2dfs[0]

		if(start == None):
			start = stock1dfs[0].iloc[-1].DATE - timedelta(days=self.momentumWindow)

		stock1Price = stock1df[stock1df.DATE >= start]
		stock2Price = stock2df[stock2df.DATE >= start]
		stock1Price = stock1Price.iloc[0][self.colName]
		stock2Price = stock2Price.iloc[0][self.colName]
		datapoint = stock1Price/stock2Price
		pastData_stock1 = stock1df[(stock1df.DATE >= (start- timedelta(days = self.pastWindow))) & (stock1df.DATE <= start)][self.colName]
		pastData_stock2 = stock2df[(stock2df.DATE >= (start- timedelta(days = self.pastWindow))) & (stock2df.DATE <= start)][self.colName]
		mean, standardDeviation = self.createDistribution(pastData_stock1, pastData_stock2)
		zscore_prev = self.calculateZScore(datapoint,mean,standardDeviation)
		momentum = (zscore - zscore_prev)/abs(zscore_prev)
		stock1Price_current = stock1df.iloc[-1][self.colName]
		stock2Price_current = stock2df.iloc[-1][self.colName]
		datapoint_current = stock1Price_current/stock2Price_current
		priceMomentum = (datapoint_current - datapoint)/abs(datapoint)
		return momentum, priceMomentum

	def get30mCandlesForTheDay(self,stock1dfs, stock2dfs):
		stock1df = stock1dfs[0]
		stock2df = stock2dfs[0]
		currentDay = stock1df.iloc[-1].DATE
		stock1df_30m = stock1dfs[1]
		stock2df_30m = stock2dfs[1]
		stock1_inTradeData = stock1df_30m[stock1df_30m.DATE == currentDay]
		stock2_inTradeData = stock2df_30m[stock2df_30m.DATE == currentDay]
		return stock1_inTradeData, stock2_inTradeData

	def get30mCandlesFromEntryPoint(self,stock1dfs, stock2dfs, entryTime):
		stock1df = stock1dfs[0]
		stock2df = stock2dfs[0]
		offset = max(self.stateConstants['momentumWindow_30m'], self.stateConstants['pastWindow_30m'])
		offsetDaily = int(np.ceil(offset/12))
		startTime = entryTime - timedelta(days=offset)
		currentTime = stock1dfs[0].iloc[-1].DATE
		stock1df_30m = stock1dfs[1]
		stock2df_30m = stock2dfs[1]
		stock1_inTradeData = stock1df_30m[(stock1df_30m.DATE >= startTime) & (stock1df_30m.DATE <= currentTime)]
		stock2_inTradeData = stock2df_30m[(stock2df_30m.DATE >= startTime) & (stock2df_30m.DATE <= currentTime)]
		intermediateValue = stock1_inTradeData[stock1_inTradeData.DATE == entryTime].iloc[-1].Datetime
		entryPos = stock1_inTradeData.index.get_loc(intermediateValue)
		return stock1_inTradeData, stock2_inTradeData, entryTime, entryPos

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

	def getNextResult(self,stock1dfs, stock2dfs, toPass = None):
		selectedEdge = 'default'
		row = None
		if(stock1dfs[0].shape[0] < self.offset):
			return selectedEdge, self.actions[selectedEdge], self.finalStates[selectedEdge],None, row

		indicators = self.preRequisites(stock1dfs, stock2dfs,toPass)
		result = None
		for edge in self.edges:
			if(edge == 'default'):
				continue
			else:
				flag, data = eval('self.' + edge + '(stock1dfs, stock2dfs,indicators, toPass)')
				if(flag):
					selectedEdge = edge
					if(self.actions[edge] == 'exitMarket'):
						if(self.stateConstants['collectRegressionData']):
							row = self.collectDataForPrediction(stock1dfs, stock2dfs, toPass)
						else:
							row = None
					break
		return selectedEdge, self.actions[selectedEdge], self.finalStates[selectedEdge],data, row