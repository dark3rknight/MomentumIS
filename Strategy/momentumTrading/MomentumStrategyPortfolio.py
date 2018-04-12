import sys
sys.path.append('/home/ishan/Desktop/Ishan/Stock Data/Code Files')
sys.path.append('/home/ishan/Desktop/Ishan/Stock Data/Code Files/Strategy')

import numpy as np
import scipy.stats as stats
import pandas as pd
import math
from datetime import datetime
from PredictiveModel import PredictiveModel
from utilities.UtilityFunctions import UtilityFunctions
from utilities.FinancialFunctions import FinancialFunctions
import os
import xlsxwriter
import random
import pandas as pd
import pickle
import matplotlib.pyplot as plt
import progressbar
from datetime import date,time,timedelta

class MomentumStrategyPortfolio:
	def __init__(self, portfolioStocks, strategyName, strategyAddress, strategyParameters, executionParameters, csvPaths, useCustomParams = False):
		exec(UtilityFunctions.initializeFunctionArguments(MomentumStrategyPortfolio.__init__))
		self.strategyObjects = {}
		self.strategyParameters = strategyParameters.copy()
		self.returnCurves = []
		self.detrendedReturnCurves = []
		self.startDate = executionParameters['startDate']
		self.endDate = executionParameters['endDate']
		self.colName = strategyParameters['PriceColumn']
		self.minimumDataPoints = strategyParameters['minimumDataPoints']
		self.numberOfDailyCandles = strategyParameters['numberOfDailyCandles']
		self.files = os.listdir(self.csvPaths[0])
		self.files.sort()
		self.returns = {}
		self.exitFlag = False
		if(not self.strategyParameters['usePredictiveModel']):
			if(self.strategyParameters['collectRegressionData']):
				self.strategyParameters['predictiveModel'] = PredictiveModel(columns = self.strategyParameters['RegressionDataColumns'], checkPoints = self.strategyParameters['checkPointRange'], saveDir = self.strategyParameters['saveRegressionDfs'])

	def testStrategy(self):
		exec('from ' + self.strategyAddress + ' import ' + self.strategyName)
		count = 0
		for stock in self.portfolioStocks:
			count += 1
			functionArguments, label,length = self.getFunctionArguments(stock)

			#Checks for file not found, minimum data points and correlation
			if(functionArguments == False):
				print('Skipping ' + label + ' as data is missing')
				self.returns[label] = '-'
				continue

			#Preparing the function string
			functionString = ''
			for i in range(len(functionArguments)):
				functionString = functionString + 'functionArguments[' + str(i) + '],'

			if(self.useCustomParams):
				params = stock[1]
				print(params)
				extra = '_'
				for key,value in params.items():
					self.strategyParameters[key] = value
					extra = extra + str(value) + '_'
				extra = extra[:-1]
			else:
				extra = ''

			print(str(count) + '. Analysing... ', label, 'Length: ' + str(length))
			strategy = eval(self.strategyName + '(parameters = self.strategyParameters)')
			returns = eval('strategy.testStrategy(' + functionString + ')')
			print(label,returns, strategy.MTMReturn_30m)
			self.stockCount['Completed'] += 1
			self.strategyObjects[label + extra] = strategy
			self.returns[label + extra] = strategy.continuousTotalReturns
			self.returnCurves.append(strategy.continuousReturnCurveWithTimeIndex)
			self.detrendedReturnCurves.append(strategy.detrendedContinuousReturnCurveWithTimeIndex_MTM)

		try:
			self.combinedCurveWithTimeIndex_MTM, self.combinedCurve_MTM, self.timeKeySet_MTM = self.combineCurves_detrended(self.detrendedReturnCurves_MTM)
			self.totalReturn_MTM = self.combinedCurve_MTM[-1]
			self.maxDrawdown_MTM = FinancialFunctions.maxDrawdown(self.combinedCurve_MTM)
			self.sharpeRatio_MTM = FinancialFunctions.sharpeRatio(self.combinedCurve_MTM, numberOfDailyCandles = self.numberOfDailyCandles)
		except IndexError:
			self.totalReturn_MTM = 0
			self.maxDrawdown_MTM = 0
			self.sharpeRatio_MTM = 0

		return self.totalReturn_MTM

	def getFunctionArguments(self,candidate):
		toReturn = []
		label = ''
		stockNames = []
		stockName = candidate
		stockNames.append(stockName)
		label = stockName
		if(stockName is int):
			stockName = self.files[stockName][:-4]
		try:
			stockdfs = []
			for csvPath in self.csvPaths:
				stockdf = pd.read_csv(csvPath + '/' + stockName + '.csv')
				stockdf['Datetime'] = stockdf['Unnamed: 0']
				stockdf.index = pd.to_datetime(stockdf['Datetime'])
				stockdf = stockdf[['DATE','TIME','CLOSE','HIGH','LOW']]
				stockdfs.append(stockdf)
		except FileNotFoundError:
			return False, label,0
		except AttributeError:
			return False, label,0

		toReturn.append(stockdfs)
		if(len(stockdfs[0]) < self.strategyParameters['minimumDataPoints']):
			return False, label, len(stockdfs[0])

		toReturn = toReturn + stockNames + [self.startDate, self.endDate]
		return toReturn, label, len(stockdfs[0])

	def calculateTotalNumberOfTrades(self, year = None):
		if(year is not None):
			return self.calculateTotalNumberOfTrades_year(year)
		totalTrades = 0
		for key,value in self.strategyObjects.items():
			strategy = value
			totalTrades += strategy.totalNumberOfTrades
		return totalTrades

	def combineCurves_detrended(self,curvesWithTimeIndex):
		continuousReturnCurve = []
		continuousReturnCurveWithTimeIndex = {}
		keySet = set([])
		for dic in curvesWithTimeIndex:
			keys = set(dic.keys())
			keySet = keySet.union(keys)
		keySet = list(keySet)
		keySet.sort()

		for key in keySet:
		    val = 0
		    num = 0
		    for i,ret in enumerate(curvesWithTimeIndex):
		        try:
		            val += ret[key]
		            num += 1
		        except KeyError:
		            a = 5
		    val = val/num
		    continuousReturnCurve.append(val)
		    continuousReturnCurveWithTimeIndex[key] = val

		prevKey = None
		for key in keySet:
			if(prevKey is not None):
				continuousReturnCurveWithTimeIndex[key] = continuousReturnCurveWithTimeIndex[key] + continuousReturnCurveWithTimeIndex[prevKey]
			else:
				continuousReturnCurveWithTimeIndex[key] = continuousReturnCurveWithTimeIndex[key]

			preKey = key

		for i in range(1,len(continuousReturnCurve)):
			continuousReturnCurve[i] = continuousReturnCurve[i] + continuousReturnCurve[i - 1] 

		return [continuousReturnCurveWithTimeIndex, continuousReturnCurve, keySet]

class MiniStrategyPortfolioObject:
	def __init__(self,strategyObject):
		self.strategyParameters = strategyObject.strategyParameters
		self.totalReturn = strategyObject.totalReturn_MTM
		self.maxDrawdown = strategyObject.maxDrawdown_MTM
		self.sharpeRatio = strategyObject.sharpeRatio_MTM

