import os
import sys
sys.path.append('/home/ishan/Desktop/Ishan/Stock Data/Code Files/Strategy')
sys.path.append('/home/ishan/Desktop/Ishan/Stock Data/Code Files')
from commonStrategyFunctions import basicFunctions as bf
from utilities import commonFunctions as cf
from StrategyPortfolio import StrategyPortfolio
from StrategyPortfolio import MiniStrategyPortfolioObject
from utilities.UtilityFunctions import UtilityFunctions
import xlsxwriter
import pickle
import numpy as np

class OptimizeStrategy:
	def __init__(self, portfolioStocks, strategyAddress, strategyName, extraParameters, strategyParameters, csvPath, initialPrint = '', logFile = None, minimumDataPoints_opt = 15000, minimumDataPoints_test = 15000, colName = 'ADJUSTED'):
		exec(UtilityFunctions.initializeFunctionArguments(OptimizeStrategy.__init__))
		self.files = os.listdir(self.csvPath)
		self.files.sort()
		self.maxResult = -10000
		self.bestCaseNeighbours = []

	def optimizeStrategy(self, parameters, parameterSpace, optimizationVariable, optimizeStartDate, optimizeEndDate, testStartDate, testEndDate, resultFile, pickleFile, neighborThreshold = 0.8):
		self.extraParameters['startDate'] = optimizeStartDate
		self.extraParameters['endDate'] = optimizeEndDate
		results = self.tryAllCombinations(parameters, parameterSpace, self.strategyParameters)

		self.calculateBestCase(results, optimizationVariable)
		self.collectBestCaseNeighbours(results, optimizationVariable, neighborThreshold)
		headRow = parameters[:] + ['Returns OPT','Drawdown OPT', 'Sharpe OPT', 'Returns Test','Drawdown Test', 'Sharpe Test']
		self.createWorkbook(resultFile, headRow)
		for strat in self.bestCaseNeighbours:
			if(strat.totalReturn == self.maxResult):
				boldFlag = True
			else:
				boldFlag = False
			previousResults = [strat.totalReturn, strat.maxDrawdown, strat.sharpeRatio]
			self.extraParameters['startDate'] = testStartDate
			self.extraParameters['endDate'] = testEndDate
			strategyPortfolio = StrategyPortfolio(self.portfolioStocks,self.strategyName, self.strategyAddress, strat.strategyParameters, self.extraParameters, self.csvPath, self.minimumDataPoints_test, colName = self.colName)
			strategyPortfolio.testStrategy()
			finalResults = [strategyPortfolio.totalReturn, strategyPortfolio.maxDrawdown, strategyPortfolio.sharpeRatio]
			row = []
			for param in parameters:
				row.append(str(strategyPortfolio.strategyParameters[param]))
			row += previousResults
			row += finalResults
			self.writeRow(boldFlag, list(row))
		self.workbook.close()
		with open(pickleFile, 'wb') as f:
			pickle.dump([self.bestCaseNeighbours,results],f)
		return self.maxResult

	def createWorkbook(self, filename, headRow):
		self.workbook = xlsxwriter.Workbook(filename)
		self.formatBold = self.workbook.add_format()
		self.formatBold.set_bold()
		self.worksheet = self.workbook.add_worksheet()
		self.worksheet.write_row('A1', headRow)
		self.rowNum = 2

	def writeRow(self,bold,row):
		if(bold):
			self.worksheet.write_row('A' + str(self.rowNum), row)
		else:
			self.worksheet.write_row('A' + str(self.rowNum), row, self.formatBold)
		self.rowNum += 1

	def tryAllCombinations(self,parameters, parameterSpace, strategyParameters = {}, toPrint = None):
		results = []
		if(not toPrint):
			toPrint = parameters
		if(len(parameters) == 0):
			strategyPortfolio = StrategyPortfolio(self.portfolioStocks,self.strategyName, self.strategyAddress, strategyParameters, self.extraParameters, self.csvPath, self.minimumDataPoints_opt, colName = self.colName)
			strategyPortfolio.testStrategy()
			printString = ''
			for arg in toPrint:
				printString += arg + ' = ' + str(strategyParameters[arg]) + ','
			print(printString + ' Result: ' + ('%.3f' % strategyPortfolio.totalReturn))
			if(self.logFile is not None):
				with open(logFile,'a') as f:
					print(printString + ' Result: ' + ('%.3f' % strategyPortfolio.totalReturn), file = f)
			return MiniStrategyPortfolioObject(strategyPortfolio.strategyParameters, strategyPortfolio.totalReturn, strategyPortfolio.maxDrawdown, strategyPortfolio.sharpeRatio)
		else:
			param = parameters[0]
			for key,val in strategyParameters.items():
				exec(key + ' = ' + str(val))
			paramSpace = eval(parameterSpace[0])
			for val in paramSpace:
				strategyParametersTemp = strategyParameters.copy()
				strategyParametersTemp[param] = val
				res = self.tryAllCombinations(parameters[1:], parameterSpace[1:], strategyParameters = strategyParametersTemp, toPrint = toPrint)
				results.append(res)
			return results

	def calculateBestCase(self, results, parameter):
		if(type(results) is not list):
			result = eval('results.' + parameter)
			if(result > self.maxResult):
				self.maxResult = result
		else:
			for i in range(len(results)):
				self.calculateBestCase(results[i],parameter)

	def collectBestCaseNeighbours(self,results,parameter, threshold):
		if(type(results) is not list):
			result = eval('results.' + parameter)
			if(self.maxResult > 0):
				if(result > self.maxResult*threshold):
					self.bestCaseNeighbours.append(results)
			else:
				if(result > self.maxResult*(1/threshold)):
					self.bestCaseNeighbours.append(results)
		else:
			for i in range(len(results)):
				self.collectBestCaseNeighbours(results[i],parameter, threshold)
