import sys
sys.path.append('/home/ishan/Desktop/Ishan/Stock Data/Code Files')
sys.path.append('/home/ishan/Desktop/Ishan/Stock Data/Code Files/Strategy')

import numpy as np
import scipy.stats as stats
import pandas as pd
import math
from datetime import datetime
from utilities import commonFunctions as cf
from utilities import Filtering as ft
from PredictiveModel import PredictiveModel
from commonStrategyFunctions import basicFunctions as bf 
import os
import xlsxwriter
import pandas as pd
import pickle
import random
import progressbar
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import LinearRegression
from sklearn import metrics
from sklearn import svm
from sklearn.cross_validation import train_test_split

class PortfolioSelection:
	def __init__(self, selectedCombinations, numberOfRandomCombinations, strategyName, strategyAddress, strategyParameters, extraParameters, stateConstants, csvPath, csvPath_30m, learningYears, testingYears, peelLengths, minimumDataPoints = 15000,colName = 'ADJUSTED', numberOfDailyCandles = 12, regressionDfPickle = None, targetDfPickle = None, splitRatio = 0.7):
		args = cf.getFunctionArguments(PortfolioSelection.__init__)
		args = args[1:]
		for arg in args:
			try:
				exec('self.' + arg + ' = ' + arg)
			except SyntaxError:
				arg = arg.split('=')
				exec('self.' + arg[0].strip() + ' = ' + arg[0].strip())

		strategyParametersString = ''
		for key,val in strategyParameters.items():
			strategyParametersString += (str(key) + ' = ' + str(val) + ',')
		self.strategyParametersString = strategyParametersString[:-1]
		files = os.listdir(self.csvPath)
		files.sort()
		columns = ['Stock 1', 'Stock 2', 'Year', 'waveCorrelation', 'waveCorrelation_30m']

		for length in peelLengths:
			columns.append('peelCorrelation_' + str(length))

		for length in peelLengths:
			columns.append('peelCorrelation_30m_' + str(length*12))

		for length in peelLengths:
			columns.append('Return_' + str(length))
			columns.append('sharpeRatio_' + str(length))


		combinations = selectedCombinations[:]
		for i in range(numberOfRandomCombinations):
		    stock1 = random.choice(files)
		    stock2 = random.choice(files)
		    combinations.append([stock1[:-4], stock2[:-4]])

		self.files = files
		self.combinations = combinations
		self.regressionDf = pd.DataFrame(columns = columns)
		self.targetDf = pd.DataFrame(columns = columns)
		self.rowNum = 0
		self.targetRowNum = 0

		print('Starting collecting features . . .')		
		self.createTrainSet(self.combinations)
		print('Finished collecting features . . .')

		print('Collecting features for prediction candidates')
		self.createTargetSet()
		print('Finished collecting features for prediction candidates')

	def createTrainSet(self, combinations):
		exec('from ' + self.strategyAddress + ' import ' + self.strategyName)
		bar = progressbar.ProgressBar()
		for stock in bar(combinations):
			try:
				functionArguments, label = self.getData(stock)
				if(len(functionArguments) == 0):
					continue
				for year in self.learningYears:
					startDate = '01/01/' + str(year)
					endDate = '31/12/' + str(year)

					stock1, stock2 = bf.selectPrices(functionArguments[0], functionArguments[1], tradeStartDate = startDate, tradeEndDate = endDate, priceColumn = self.colName)
					if(len(stock1) < self.minimumDataPoints):
						continue

					startDate_corr = '01/01/' + str(year - 1)
					endDate_corr = '31/12/' + str(year - 1)

					try:
						waveCorrelation, peelCorrelations = self.getCorrelations(functionArguments[0],functionArguments[1], startDate_corr, endDate_corr, self.peelLengths)
						waveCorrelation_30, peelCorrelations_30 = self.getCorrelations(functionArguments[2],functionArguments[3], startDate_corr, endDate_corr, [length*12 for length in self.peelLengths])
					except ValueError:
						continue
					except TypeError:
						continue

					data = []
					for pastWindow in self.peelLengths:
						self.stateConstants['pastWindow'] = pastWindow
						functionArgumentsNew = functionArguments[:]
						functionArgumentsNew.append(startDate)
						functionArgumentsNew.append(endDate)
						functionString = ''
						for i in range(len(functionArgumentsNew)):
							functionString = functionString + 'functionArgumentsNew[' + str(i) + '],'
						if(self.extraParameters['transactionSummary']):
							self.strategyParametersString_forStock = self.strategyParametersString + (',transactionSummary = "' + cf.makeDir(self.extraParameters['transactionSummaryFolder']) + '/TS_' + functionArguments[2] + '_' + functionArguments[3] + '.xlsx"')
						else:
							self.strategyParametersString_forStock = self.strategyParametersString
						if(self.extraParameters['positionSummary']):
							self.strategyParametersString_forStock += (',positionSummary = "' + cf.makeDir(self.extraParameters['positionSummaryFolder']) + '/PS_' + functionArguments[2] + '_' + functionArguments[3] + '.xlsx"')
						print('Analysing... ', label, pastWindow,year, 'Correlation: ', '%.3f' % waveCorrelation)
						strategy = eval(self.strategyName + '(' + self.strategyParametersString_forStock + ', stateConstants = self.stateConstants)')
						returns = eval('strategy.testStrategy(' + functionString + ')')
						data.append(returns)
						data.append(strategy.sharpeRatio_continuous)
						print(pastWindow,label,returns)

					row = [label.split(' ')[0], label.split(' ')[1], year, waveCorrelation, waveCorrelation_30]
					row = row + peelCorrelations + peelCorrelations_30 + data

					self.regressionDf.loc[self.rowNum] = row
					self.rowNum += 1
					if(self.regressionDfPickle):
						with open(self.regressionDfPickle, 'wb') as f:
							pickle.dump(self.regressionDf, f)
			except:
				continue

	def createTargetSet(self):
		exec('from ' + self.strategyAddress + ' import ' + self.strategyName)
		bar = progressbar.ProgressBar()
		combinations = []
		for i in range(len(self.files)):
			for j in range(i,len(self.files)):
				combinations.append([self.files[i][:-4], self.files[j][:-4]])

		for stock in bar(combinations):
			startDate_corr = '01/01/' + str(2017)
			endDate_corr = '31/12/' + str(2017)
			functionArguments, label = self.getData(stock)
			stock1, stock2 = bf.selectPrices(functionArguments[0], functionArguments[1], tradeStartDate = startDate_corr, tradeEndDate = endDate_corr, priceColumn = self.colName)

			if(len(stock1) < 10):
				continue

			waveCorrelation, peelCorrelations = self.getCorrelations(functionArguments[0],functionArguments[1], startDate_corr, endDate_corr, self.peelLengths)
			waveCorrelation_30, peelCorrelations_30 = self.getCorrelations(functionArguments[2],functionArguments[3], startDate_corr, endDate_corr, [length*12 for length in self.peelLengths])
			row = [label.split(' ')[0], label.split(' ')[1], '2017', waveCorrelation, waveCorrelation_30]
			row = row + peelCorrelations + peelCorrelations_30
			row = row + ['-']*len(self.peelLengths)*2

			self.targetDf.loc[self.targetRowNum] = row
			self.targetRowNum += 1
			if(self.targetDfPickle):
				with open(self.targetDfPickle, 'wb') as f:
					pickle.dump(self.targetDf, f)

	def getCorrelations(self,stock1df, stock2df, startDate, endDate, peelLengths):
		stock1, stock2 = bf.selectPrices(stock1df, stock2df, tradeStartDate = startDate, tradeEndDate = endDate, priceColumn = self.colName)
		waveCorrelation = stats.pearsonr(stock1, stock2)[0]
		peelCorrelations = []
		for length in peelLengths:
			smooth_data1,peel1 = ft.savitzkyGolay(stock1,[length + 1,5])
			smooth_data2,peel2 = ft.savitzkyGolay(stock2,[length + 1,5])
			peelCorrelations.append(stats.pearsonr(peel1, peel2)[0])

		return waveCorrelation, peelCorrelations

	def createPredictiveModel(self, modType = 'Logistic', splitRatio = 0.4, param = None):
		predModel = PredictiveModel(self.regressionDf)
		if(param == None):
			logModel, trainScore, testScore, truePositives, trueNegatives = eval('predModel.create'+ modType +'Model(splitRatio = self.splitRatio)')
		else:
			logModel, trainScore, testScore, truePositives, trueNegatives = eval('predModel.create'+ modType +'Model(splitRatio = self.splitRatio, param = param)')
		print('Results from the Predictive Model: \nTraining:', trainScore,'\nTest:', testScore,'\nTrue Positives:', truePositives,'\nTrue Negatives:',  trueNegatives)
		return logModel

	def saveRegressionDF(self,filename):
		with open(filename, 'wb') as f:
			pickle.dump(self.regressionDf, f)

	def saveRegressionDFasCSV(self,filename):
		self.regressionDf.to_csv(filename)

	def saveLogModel(self,filename):
		with open(filename, 'wb') as f:
			pickle.dump(self.logModel, f)

	def getData(self,candidate):
		stockName1 = candidate[0]
		stockName2 = candidate[1]

		if(stockName1 is int):
			stockName1 = self.files[stockName1][:-4]
			stockName2 = self.files[stockName2][:-4]
		try:
			stock1df = pd.read_csv(self.csvPath + '/' + stockName1 + '.csv')
			stock1df.index = pd.to_datetime(stock1df.Datetime)
			stock1df_30m = pd.read_csv(self.csvPath_30m + '/' + stockName1 + '.csv')
			stock1df_30m.index = pd.to_datetime(stock1df_30m.Datetime)
		except FileNotFoundError:
			return [], stockName1 + ' ' + stockName2

		try:
			stock2df = pd.read_csv(self.csvPath + '/' + stockName2 + '.csv')
			stock2df.index = pd.to_datetime(stock2df.Datetime)
			stock2df_30m = pd.read_csv(self.csvPath_30m + '/' + stockName2 + '.csv')
			stock2df_30m.index = pd.to_datetime(stock2df_30m.Datetime)
		except FileNotFoundError:
			return [],stockName1 + ' ' + stockName2

		stock1df = stock1df[[self.colName]]
		stock2df = stock2df[[self.colName]]
		stock1df_30m = stock1df_30m[[self.colName]]
		stock2df_30m = stock2df_30m[[self.colName]]
		functionArguments = [stock1df, stock2df,stock1df_30m, stock2df_30m, stockName1, stockName2]
		return functionArguments, stockName1 + ' ' + stockName2

	def createModel(df,splitRatio, trainFeatures, targetFeature):
		train_x, test_x, train_y, test_y = train_test_split(df[trainFeatures], df[targetFeature], train_size=splitRatio)
		logistic_regression_model = svm.SVC(class_weight = 'balanced', multi_class='multinomial')
		logistic_regression_model.fit(train_x, train_y)
		predictedResults = logistic_regression_model.predict(test_x)
		print(logistic_regression_model.predict_proba(test_x))
		print(metrics.accuracy_score(test_y, predictedResults))
		print(metrics.confusion_matrix(test_y, predictedResults))
		print(test_y.value_counts())
		return True

