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

class StrategyPortfolio:
	def __init__(self, portfolioStocks, strategyName, strategyAddress, strategyParameters, executionParameters, csvPaths, useCustomParams = False):
		exec(UtilityFunctions.initializeFunctionArguments(StrategyPortfolio.__init__))
		self.strategyObjects = {}
		self.strategyParameters = strategyParameters.copy()
		self.returnCurves = []
		self.detrendedReturnCurves = []
		self.detrendedReturnCurves_MTM = []
		self.combinationsSkipped = []
		self.startDate = executionParameters['startDate']
		self.endDate = executionParameters['endDate']
		self.colName = strategyParameters['colName']
		self.minimumDataPoints = strategyParameters['minimumDataPoints']
		self.numberOfDailyCandles = strategyParameters['numberOfDailyCandles']
		self.stockCount = {'Completed': 0, 'Missing Data': 0, 'Low Correlation': 0}
		self.files = os.listdir(self.csvPaths[0])
		self.files.sort()
		self.returns = {}
		self.exitFlag = False
		if(self.strategyParameters['usePredictiveModel']):
			self.logModelExists = os.path.exists(eval(self.strategyParameters['predictiveModel']))
			if(self.logModelExists):
				with open(eval(self.strategyParameters['predictiveModel']), 'rb') as f:	
					self.strategyParameters['predictiveModel'] = pickle.load(f)
			else:
				fileName = self.strategyParameters['predictiveModel']
				model = self.trainRegressionModel(eval(fileName))
				if(model is None):
					self.exitFlag = True
				else:
					self.strategyParameters['predictiveModel'] = model
		else:
			if(self.strategyParameters['collectRegressionData']):
				self.strategyParameters['predictiveModel'] = PredictiveModel(columns = self.strategyParameters['RegressionDataColumns'], checkPoints = self.strategyParameters['checkPointRange'], saveDir = self.strategyParameters['saveRegressionDfs'])

	def testStrategy(self):
		if(self.exitFlag):
			self.totalReturn_MTM = 0
			self.maxDrawdown_MTM = 0
			self.sharpeRatio_MTM = 0
			return 0

		exec('from ' + self.strategyAddress + ' import ' + self.strategyName)
		count = 0
		for stock in self.portfolioStocks:
			count += 1
			functionArguments, label = self.getFunctionArguments([stock[0],stock[1]])
			#Checks for file not found, minimum data points and correlation
			if(functionArguments == False):
				print('Skipping ' + label + ' as data is missing')
				self.combinationsSkipped.append(stock)
				self.stockCount['Missing Data'] += 1
				self.returns[label] = '-'
				continue
			else:
				length, proceedFlag = self.doesPairMeetConditions(functionArguments[0][0], functionArguments[1][0])
				if(not proceedFlag):
					print('Skipping ' + label + ' as length: '+ str(length))
					self.combinationsSkipped.append(stock)
					self.stockCount['Low Correlation'] += 1
					self.returns[label] = '-'
					continue

			#Preparing the function string
			functionString = ''
			for i in range(len(functionArguments)):
				functionString = functionString + 'functionArguments[' + str(i) + '],'

			if(self.useCustomParams):
				params = stock[2]
				print(params)
				extra = '_'
				for key,value in params.items():
					self.strategyParameters[key] = value
					extra = extra + str(value) + '_'
				extra = extra[:-1]
				extra = ''
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
			self.detrendedReturnCurves.append(strategy.detrendedContinuousReturnCurveWithTimeIndex)
			self.detrendedReturnCurves_MTM.append(strategy.detrendedContinuousReturnCurveWithTimeIndex_MTM)

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

	def trainRegressionModel(self, fileName):
		exec('from ' + self.strategyAddress + ' import ' + self.strategyName)
		print('Regression Model was not available. Learning the regression model.\n', self.strategyParameters)
		with open('./Strategy/logModels/regressionTrainingData.pickle','rb') as f:
			trainingPortfolioStocks, trainStartDate, trainEndDate, trainingMinimumDataPoints, ratioLimit, trainFeatures, targetFeature, splitRatio = pickle.load(f)

		tempStartDate = self.startDate
		tempEndDate = self.endDate
		tempMinimumDataPoints = self.minimumDataPoints
		tempPredictiveModel = self.strategyParameters['predictiveModel']
		tempCollectRegressionData = self.strategyParameters['collectRegressionData']

		self.minimumDataPoints = trainingMinimumDataPoints
		self.startDate = trainStartDate
		self.endDate = trainEndDate
		self.strategyParameters['predictiveModel'] = PredictiveModel(columns = self.strategyParameters['RegressionDataColumns'])
		self.strategyParameters['collectRegressionData'] = True
		self.strategyParameters['usePredictiveModel'] = False

		randomizedFlag = False
		count = 0
		while(count < len(trainingPortfolioStocks)):
			if(not randomizedFlag):
				stock = trainingPortfolioStocks[count]
			else:
				stock = [random.choice(self.files)[:-4], random.choice(self.files)[:-4]]

			functionArguments, label = self.getFunctionArguments(stock)
			if((functionArguments == False) or (stock[0] == stock[1])):
				count += 1
				continue
			else:
				length, proceedFlag = self.doesPairMeetConditions(functionArguments[0][0], functionArguments[1][0])
				if(not proceedFlag):
					count += 1
					continue
			functionString = ''
			for i in range(len(functionArguments)):
				functionString = functionString + 'functionArguments[' + str(i) + '],'

			print('Analysing... ', label, 'Length: ' + str(length))
			strategy = eval(self.strategyName + '(parameters = self.strategyParameters)')
			returns = eval('strategy.testStrategy(' + functionString + ')')
			print(label,returns)

			ratio = self.strategyParameters['predictiveModel'].getPositiveToNegativeRatio(targetFeature)
			if(ratio > ratioLimit):
				randomizedFlag = True
			else:
				randomizedFlag = False
				count += 1

		try:
			model = self.strategyParameters['predictiveModel'].createLogisticModel(trainFeatures, targetFeature, splitRatio = splitRatio)
			self.strategyParameters['predictiveModel'].saveLogModel(fileName)
			self.startDate = tempStartDate
			self.endDate = tempEndDate
			self.minimumDataPoints = tempMinimumDataPoints
			self.strategyParameters['collectRegressionData'] = tempCollectRegressionData
			self.strategyParameters['usePredictiveModel'] = True
			self.strategyParameters['predictiveModel'] = tempPredictiveModel
			return model
		except ValueError:
			self.startDate = tempStartDate
			self.endDate = tempEndDate
			self.minimumDataPoints = tempMinimumDataPoints
			self.strategyParameters['collectRegressionData'] = tempCollectRegressionData
			self.strategyParameters['usePredictiveModel'] = True
			self.strategyParameters['predictiveModel'] = tempPredictiveModel
			return None		

	def getFunctionArguments(self,candidate):
		toReturn = []
		label = ''
		stockNames = []
		for i in range(len(candidate)):
			stockName = candidate[i]
			stockNames.append(stockName)
			label = label + ' ' + stockName
			if(stockName is int):
				stockName = self.files[stockName][:-4]
			try:
				stockdfs = []
				for csvPath in self.csvPaths:
					stockdf = pd.read_csv(csvPath + '/' + stockName + '.csv')
					stockdf.index = pd.to_datetime(stockdf.Datetime)
					stockdf.DATE = pd.to_datetime(stockdf.DATE)
					stockdf.DATE = stockdf.DATE.dt.date
					stockdfs.append(stockdf)
			except FileNotFoundError:
				return False, label
			except AttributeError:
				return False, label
			toReturn.append(stockdfs)

		toReturn = toReturn + stockNames + [self.startDate, self.endDate]
		return toReturn, label[1:]

	def doesPairMeetConditions(self,stock1df, stock2df):
		stock1, stock2 = UtilityFunctions.selectData(stock1df, stock2df, tradeStartDate = self.startDate, tradeEndDate = self.endDate)
		if(len(stock1) > self.minimumDataPoints):
			flag = True
		else:
			flag = False

		return len(stock1), flag

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

	def createExcel_ForYogesh(self,fileName1, startDate, endDate):
		workbook1 = xlsxwriter.Workbook(fileName1)
		worksheet1 = workbook1.add_worksheet()
		headRow1 = ['Datetime']
		headRow2 = ['']
		headRow3 = ['']
		for key,value in self.strategyObjects.items():
			if(self.useCustomParams):
				stock1 = key.split(' ')[0]
				elements = key.split(' ')[1].split('_')
				stock2 = elements[0]
				ma = elements[1]
				zs = elements[2]
				tp = elements[3]
			else:
				stock1 = key.split(' ')[0]
				stock2 = key.split(' ')[1]
				ma = ''
				zs = ''
				tp = ''
			headRow1.append(stock1)
			headRow1.append(stock2)
			headRow2.append(ma)
			headRow2.append(zs)
			headRow3.append(tp)
			headRow3.append('')
		worksheet1.write_row('A1',headRow1)
		worksheet1.write_row('A2',headRow2)
		worksheet1.write_row('A3',headRow3)
		rowCount = 4
		bar = progressbar.ProgressBar()
		for date in bar(UtilityFunctions.daterange(startDate, endDate + timedelta(days = 1))):
			for tm in UtilityFunctions.timerange(time(9,30), time(15,30), timedelta(minutes = 30)):
				row1 = [str(datetime.combine(date,tm))]
				minFlag = True
				for key,value in self.strategyObjects.items():
					if(datetime.combine(date,tm) in value.positionsWithTimeIndex.keys()):
						row1.append(value.positionsWithTimeIndex[datetime.combine(date,tm)])						
						row1.append(value.MTMWithTimeIndex[datetime.combine(date,tm)])
						minFlag = True
					else:
						row1.append('NA')
						row1.append('NA')
				if(minFlag):
					worksheet1.write_row('A' + str(rowCount), row1)
					rowCount += 1
		workbook1.close()

	def createSummaryExcel(self,filename):
		workbook = xlsxwriter.Workbook(filename)
		worksheet = workbook.add_worksheet('Return Curve')
		worksheet.write_row('A1', ['Date','Return'])
		returnCurve = self.combinedCurveWithTimeIndex_MTM
		keySet = list(returnCurve.keys())
		keySet.sort()
		rowCount = 2
		for key in keySet:
			row = [str(key), returnCurve[key]]
			worksheet.write_row('A' + str(rowCount), row)
			rowCount += 1
		worksheet = workbook.add_worksheet('Results')
		worksheet.write_row('A1', ['Return','Drawdown', 'Sharpe'])
		worksheet.write_row('A2', ['%.3f' % self.totalReturn_MTM,'%.3f' % self.maxDrawdown_MTM, '%.3f' % self.sharpeRatio_MTM])
		workbook.close()

class MiniStrategyPortfolioObject:
	def __init__(self,strategyObject):
		self.strategyParameters = strategyObject.strategyParameters
		self.totalReturn = strategyObject.totalReturn_MTM
		self.maxDrawdown = strategyObject.maxDrawdown_MTM
		self.sharpeRatio = strategyObject.sharpeRatio_MTM

