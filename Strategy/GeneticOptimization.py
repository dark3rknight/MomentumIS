import os
import sys
sys.path.append('/home/ishan/Desktop/Ishan/Stock Data/Code Files/Strategy')
sys.path.append('/home/ishan/Desktop/Ishan/Stock Data/Code Files')
from commonStrategyFunctions import basicFunctions as bf
from utilities import commonFunctions as cf
from StrategyPortfolio import StrategyPortfolio
from StrategyPortfolio import MiniStrategyPortfolioObject
from utilities.UtilityFunctions import UtilityFunctions
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import xlsxwriter
import pickle
import numpy as np
import pandas as pd
import random

class GeneticOptimization:
	def __init__(self, portfolioStocks, strategyDetails ,executionParameters, optimizingVariables, loggerAddresses = None):
		exec(UtilityFunctions.initializeFunctionArguments(GeneticOptimization.__init__))
		self.strategyAddress, self.strategyName, self.strategyData, self.strategyParameters, self.csvPaths = strategyDetails
		self.categoricalVariables, self.continuousVariables, self.variableBindings, self.integerOnlyParameters, self.roundOffs, self.optimizeStartDate, self.optimizeEndDate, self.testStartDate, self.testEndDate, self.parameter, self.direction = optimizingVariables
		self.numberOfStocksPerIndividual, self.numberOfGenerations, self.targetFitness, self.parameter, self.degreeOfVariability, self.minimumDataPoints, self.numberOfFittest, self.startingPopulation, self.newKids, self.inheritedKidsPerFather = executionParameters
		self.detailedLogger, self.summarisedLogger, self.chartAddress = loggerAddresses
		self.currentBest = [-10000000000000,None]
		self.currentBestCurve = [[],[],[]]
		self.currentBestCurveTest = [[],[],[]]
		self.currentBestTest = [-10000000000,None]
		self.strategyData['startDate'] = self.optimizeStartDate
		self.strategyData['endDate'] = self.optimizeEndDate
		self.files = os.listdir(self.csvPaths[0])
		self.files.sort()
		self.selectedStocks = self.createSubList()
		self.fittestIndividuals = None
		self.generationCount = 0
		self.combinationsDone = {}

	def processNextGeneration(self):
		self.generationCount += 1
		generation = self.createGeneration()
		evaluatedGeneration = self.evaluateGeneration(generation)
		self.fittestIndividuals = self.selectFittestIndividuals(evaluatedGeneration)
		bestResults = self.getFittestResult()
		self.updateData()
		if(self.chartAddress):
			self.plotChart()
		return self.currentBest

	def masterExecutor(self):
		if(len(self.selectedStocks) == 0):
			return None
		if(self.targetFitness is None)and(self.numberOfGenerations is None):
			raise ValueError('Both target fitess and number of generations cannot be None. Please specify when should the code exit.')

		while((self.targetFitness is None) or (self.currentBest[0]*self.direction < self.targetFitness*self.direction))and((self.numberOfGenerations is None) or (self.generationCount < self.numberOfGenerations)):
			print('Processing Generation', self.generationCount + 1)
			self.processNextGeneration()

		return self.currentBest

	def updateData(self):
		self.currentBestCurve[0].append(self.currentBest[1].totalReturn)
		self.currentBestCurveTest[0].append(self.currentBestTest[1].totalReturn)

		self.currentBestCurve[1].append(self.currentBest[1].maxDrawdown)
		self.currentBestCurveTest[1].append(self.currentBestTest[1].maxDrawdown)

		self.currentBestCurve[2].append(self.currentBest[1].sharpeRatio)
		self.currentBestCurveTest[2].append(self.currentBestTest[1].sharpeRatio)

	def plotChart(self):
		gs = gridspec.GridSpec(1,3)
		plt.close()
		plt.figure(figsize = (12,4))
		plt.subplot(gs[0,0])
		plt.plot(self.currentBestCurve[0], color = 'blue', label = 'Training Set', marker = '.')
		plt.plot(self.currentBestCurveTest[0], color = 'red', label = 'Test Set', marker = '.')
		plt.title('Total Return')
		plt.legend()

		plt.subplot(gs[0,1])
		plt.plot(self.currentBestCurve[1], color = 'blue', label = 'Training Set', marker = '.')
		plt.plot(self.currentBestCurveTest[1], color = 'red', label = 'Test Set', marker = '.')
		plt.title('Max Drawdown')
		plt.legend()

		plt.subplot(gs[0,2])
		plt.plot(self.currentBestCurve[2], color = 'blue', label = 'Training Set', marker = '.')
		plt.plot(self.currentBestCurveTest[2], color = 'red', label = 'Test Set', marker = '.')
		plt.title('Sharpe Ratio')
		plt.legend()

		plt.tight_layout()
		plt.savefig(self.chartAddress)

	def evaluateGeneration(self,generation):
		population = []
		count = 0
		for gen in generation:
			result = None
			count += 1
			genCompact = self.createCompactGen(gen)
			if(hash(frozenset(genCompact.items())) in self.combinationsDone.keys()):
				result = self.combinationsDone[hash(frozenset(genCompact.items()))]

			if(result is None):
				strategyPortfolio = StrategyPortfolio(self.selectedStocks,self.strategyName, self.strategyAddress, gen, self.strategyData, self.csvPaths)
				strategyPortfolio.testStrategy()
				result = MiniStrategyPortfolioObject(strategyPortfolio)
				self.combinationsDone[hash(frozenset(genCompact.items()))] = result

			if(self.detailedLogger):
				with open(self.detailedLogger + '/generation_' + str(self.generationCount) + '.txt','a') as f:
					print(str(count) + '. \t', genCompact, '\n', 'Returns: ' + ('%.3f' % result.totalReturn) + '\n',  'Max Drawdown: ' + ('%.3f' % result.maxDrawdown) + '\n',  'Sharpe Ratio: ' + ('%.3f' % result.sharpeRatio) + '\n\n\n\n', file = f)
			population.append(result)
		return population

	def createCompactGen(self,gen):
		toReturn = {}
		for val in self.categoricalVariables:
			toReturn[val] = gen[val]

		for val in self.continuousVariables:
			toReturn[val] = gen[val]

		return toReturn

	def getFittestResult(self):
		results = []
		for individual in self.fittestIndividuals:
			result = eval('individual.' + self.parameter)
			results.append(result)
			if(result > self.currentBest[0]):
				print('Found new best: ', '%.3f' % result)
				self.currentBest = [result, individual]
			self.strategyDataTest = self.strategyData.copy()
			self.strategyDataTest['startDate'] = self.testStartDate
			self.strategyDataTest['endDate'] = self.testEndDate
			self.strategyParametersTest = self.currentBest[1].strategyParameters.copy()
			self.strategyParametersTest['predictiveModel'] = self.strategyParameters['predictiveModel']
			strategyPortfolio = StrategyPortfolio(self.portfolioStocks,self.strategyName, self.strategyAddress, self.strategyParametersTest, self.strategyDataTest, self.csvPaths)
			strategyPortfolio.testStrategy()
			bestCase = MiniStrategyPortfolioObject(strategyPortfolio)
			self.currentBestTest = [eval('bestCase.' + self.parameter), bestCase]

		if(self.detailedLogger):
			with open(self.detailedLogger + '/generation_' + str(self.generationCount) + '.txt','a') as f:
				print('Fittest Individual \n', self.createCompactGen(self.currentBest[1].strategyParameters), '\n', 'Returns: ' + ('%.3f' % self.currentBest[1].totalReturn) + '\t' + ('%.3f' % self.currentBestTest[1].totalReturn) + '\n',  'Max Drawdown: ' + ('%.3f' % self.currentBest[1].maxDrawdown) + '\t' + ('%.3f' % self.currentBestTest[1].maxDrawdown) + '\n',  'Sharpe Ratio: ' + ('%.3f' % self.currentBest[1].sharpeRatio) +'\t' + ('%.3f' % self.currentBestTest[1].sharpeRatio) +  '\n', file = f)
	
		if(self.summarisedLogger):
			with open(self.summarisedLogger,'a') as f:
				print('Generation ' + str(self.generationCount),'\n', 'Returns: ' + ('%.3f' % self.currentBest[1].totalReturn) + '\t' + ('%.3f' % self.currentBestTest[1].totalReturn) + '\n',  'Max Drawdown: ' + ('%.3f' % self.currentBest[1].maxDrawdown) + '\t' + ('%.3f' % self.currentBestTest[1].maxDrawdown) + '\n',  'Sharpe Ratio: ' + ('%.3f' % self.currentBest[1].sharpeRatio) +'\t' + ('%.3f' % self.currentBestTest[1].sharpeRatio) +  '\n', file = f)
		return results

	def selectFittestIndividuals(self,generation):
		fittest = []
		toCheck = []
		bests = []
		for i in range(self.numberOfFittest):
			bestCase = -100000000*self.direction
			bestIndividual = None
			for individual in generation:
				fitness = eval('individual.' + self.parameter)
				if(i==0):
					toCheck.append(fitness)
				if(fitness != fitness):
					continue
				if((fitness*self.direction > bestCase)and(individual not in fittest)):
					bestCase = fitness
					bestIndividual = individual
			fittest.append(bestIndividual)
		for ind in fittest:
			bests.append(eval('ind.' + self.parameter))
		print(toCheck, bests)
		return fittest

	def generateRandomizedIndividual(self):
		parameters = self.strategyParameters.copy()
		for key,value in self.categoricalVariables.items():
			print(value)
			value = eval(value)
			parameters[key] = random.choice(value)

		for key,value in self.continuousVariables.items():
			value = eval(value)
			if(key in self.variableBindings.keys()):
				decidingKey = self.variableBindings[key]
				if(parameters[decidingKey] == False):
					continue
			parameters[key] = int(random.choice(value)) if (key in self.integerOnlyParameters) else round(random.choice(value), self.roundOffs[key])
		return parameters

	def inheritedIndividual(self,father):
		parameters = self.strategyParameters.copy()
		for key,value in self.categoricalVariables.items():
			parameters[key] = father.strategyParameters[key]

		for key,value in self.continuousVariables.items():
			value = eval(value)
			if(key in self.variableBindings.keys()):
				decidingKey = self.variableBindings[key]
				if(parameters[decidingKey] == False):
					continue
			val = father.strategyParameters[key]
			valRange = (max(value) - min(value))
			deviation = valRange*(self.degreeOfVariability/100)
			draw = np.random.normal(loc = val, scale = deviation)
			parameters[key] = int(self.findClosest(value,draw)) if (key in self.integerOnlyParameters) else round(self.findClosest(value,draw), self.roundOffs[key])
		return parameters

	def findClosest(self,vals, number):
	    if(number in vals):
	        return number
	    flag = True
	    lowerLimit = 0
	    upperLimit = len(vals) - 1
	    index = int((upperLimit + lowerLimit)/2)
	    while(flag):
	        if(number <= vals[index + 1])and(number >= vals[index]):
	            return vals[index] if (number - vals[index] < vals[index + 1] - number) else vals[index + 1]
	        else:
	            if(number < vals[index]):
	                upperLimit = index
	            else:
	                lowerLimit = index
	        
	        index = int((upperLimit + lowerLimit)/2)
	        if(index < 1):
	            return vals[0]

	        if(index >= len(vals) - 2):
	            return vals[-1]

	def createGeneration(self):
		generation = []
		for i in range(self.newKids):
			generation.append(self.generateRandomizedIndividual())
		if(self.fittestIndividuals is not None):
			for father in self.fittestIndividuals:
				for i in range(self.inheritedKidsPerFather):
					generation.append(self.inheritedIndividual(father))
		else:
			for i in range(self.startingPopulation - self.newKids):
				generation.append(self.generateRandomizedIndividual())
			
		if(self.currentBest[1] is not None):
			for i in range(self.inheritedKidsPerFather*2):
				generation.append(self.inheritedIndividual(self.currentBest[1]))
		return generation

	def createSubList(self):
		selectedStocks = []
		checkCount = 0
		while((len(selectedStocks) != self.numberOfStocksPerIndividual)and(checkCount != len(self.portfolioStocks))):
			stock = random.choice(self.portfolioStocks)
			if(stock in selectedStocks):
				continue
			functionArguments, label = self.getFunctionArguments(stock)
			if(functionArguments == False):
				checkCount += 1
				continue
			else:
				if(not self.doesPairMeetConditions(functionArguments[0][0], functionArguments[1][0])):
					checkCount += 1
					continue
				else:
					selectedStocks.append(stock)
			checkCount += 1
		return selectedStocks

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
			toReturn.append(stockdfs)
		return toReturn, label[1:]

	def doesPairMeetConditions(self,stock1df, stock2df):
		stock1, stock2 = UtilityFunctions.selectData(stock1df, stock2df, tradeStartDate = self.optimizeStartDate, tradeEndDate = self.optimizeEndDate)
		if(len(stock1) > self.minimumDataPoints):
			flag = True
		else:
			flag = False
		return flag
