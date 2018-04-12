import pandas as pd
import numpy as np
import os
import sys
currentDir = os.getcwd()
sys.path.append(currentDir + '/Strategy')
sys.path.append(currentDir + '/Strategy/momentumTrading')
from Strategy import Strategy
from datetime import datetime
from momentumTrading.MomentumAutomata import MomentumAutomata
from Trade import Trade
from utilities.UtilityFunctions import UtilityFunctions
import progressbar
from datetime import timedelta, time, date

class MomentumStrategy(Strategy):
	def __init__(self, parameters = None):
		Strategy.__init__(self, None, None,None, parameters = parameters)
		exec(UtilityFunctions.initializeFunctionArguments(MomentumStrategy.__init__))
		defaultparameters = {'zscoreBuy':2, 'zscoreSell':0, 'zscoreStopLoss':3.5, 'correlationSelectionThreshold':0.3, 'stopLossFlag':True, 'correlationCheckFlag':True, 'pastWindow':40, 'momentumCheck':False, 'momentumWindow':40, 'momentumThresholds':[20,80],'momentumCheckWaitWindow':10, 'almostRevertedFlag':False, 'zscoreAlmostMeanReverted':0.1, 'colName': 'EQUITY', 'numberOfDailyCandles': 1, 'automataFile': './pairsTrading/pairsTrading_automata.csv', 'transactionSummary': None, 'positionSummary': None}
		self.parameters = UtilityFunctions.fillDefaultData(parameters, defaultparameters)

		#Constatnts
		self.offset = np.max([self.parameters['smba_period1'], self.parameters['smba_period2'], self.parameters['ols_period']])
		self.colName = self.parameters['colName']
		self.automata = MomentumAutomata(self.parameters['automataFile'])
		self.numberOfDailyCandles = self.parameters['numberOfDailyCandles']
		self.transactionSummary = self.parameters['transactionSummary']
		self.positionSummary = self.parameters['positionSummary']
		self.parameters['offset'] = self.offset
		self.positionsWithTimeIndex = {}
		self.predictiveModelDataRow = None
		self.MTMReturn_30m = 0
		self.MTMWithTimeIndex = {}

		#Data Collectors
		self.correlations = [np.nan]*self.offset
		self.zscores = [np.nan]*self.offset
		self.priceRatios = [np.nan]*self.offset
		self.priceRatioMomentums = [np.nan]*self.offset
		self.momentumValues = [np.nan]*self.offset

		self.profitDistributions = {}
		for states, edges in self.automata.edges.items():
			for edge in edges:
				self.profitDistributions[edge] = [0,0]
		self.profitDistributions['residue'] = [0,0]

		self.continuousReturnCurve = []

		#Creating excel files
		if(self.transactionSummary):
			headRow = ['Start Time','End Time','Buy Price','Sell Price','Profit']
			self.workbook, self.worksheet, self.formatRed = self.createTransactionFile(self.transactionSummary, headRow, sheetName)
			self.tsRowNumber = 2
		else:
			self.workbook, self.worksheet, self.formatRed = [None,None,None]


		if(self.positionSummary):
			headRow = ['Datetime','Price','Position','Return Curve']
			self.positionWorkbook, self.positionWorksheet, self.positionFormatRed = self.createTransactionFile(self.positionSummary, headRow, sheetName)
			self.psRowNumber = 2
		else:
			self.positionWorkbook, self.positionWorksheet, self.positionFormatRed = [None,None,None]

	def testStrategy(self,stockdf, stockName = None, startDate = None, endDate = None):
		stockdf = stockdf[0]
		self.stockdf = stockdf
		self.stockName = stockName
		self.automata.initializeStates(self.parameters, stockdf)
		bar = progressbar.ProgressBar()
		startDate = np.min(stockdf.DATE)
		endDate = np.max(stockdf.DATE)
		for datetime in bar(UtilityFunctions.datetimerange(startDate, endDate, parameters['timeDelta'])):
			self.positionUpdateDone = False
			data = UtilityFunctions.getData_Date(stockdfs, date)
			if(len(data[0]) == 0):
				continue
			selectedEdge,action,currentState,data, row = self.automata.generateDecision(data)
			self.predictiveModelDataRow = row
			if(action != 'continue'):
				exec('self.' + action + '(datetime,data,selectedEdge)')
			if(data != None):
				self.updateData(datetime,data,selectedEdge)
		return self.closingFormalities()

	def exitAndEnterMarket(self,datetime,data,selectedEdge):
		self.exitMarket(datetime,data,selectedEdge)
		self.enterMarket(datetime,data,selectedEdge)

	def enterMarket(self,datetime,data,selectedEdge):
		self.direction = data['direction']
		self.stock = self.stockName
		self.price = data['price']
		self.ongoingTrade = Trade(self.sellPrice, direction = self.direction)
		self.entryTime = datetime

	def exitMarket(self,datetime,data = None,selectedEdge = None):
		profit, profitMTMs = self.ongoingTrade.exitTrade(data['price'])
		self.detrendedContinuousReturnCurveWithTimeIndex_MTM[datetime] = profitMTM
		self.continuousImmediateReturn = profitMTMs[0]
		self.continuousTotalReturns += profitMTMs[0]
		self.exitTime = datetime
		self.immediateReturn = profit

		if(self.workbook):
			row = [str(self.entryTime), str(self.exitTime), '%.3f' % self.price, '%.3f' % data['price'], '%.3f' % profit]
			self.writeTransaction(profit, row, self.worksheet, self.formatRed)

		if(self.predictiveModelDataRow):
			for cP, row in self.predictiveModelDataRow.items():
				newRow = [(self.exitTime - self.entryTime).days] + row + [profit, (1 if (profit > 0) else 0),(1 if ((profit - row[-5]) > 0) else 0)]
				self.parameters['predictiveModel'].add(newRow, cP)
			self.predictiveModelDataRow = None

		self.ongoingTrade = None
		self.price = None
		self.returnListWithTime.append([profit,self.entryTime, self.exitTime, self.direction])
		self.direction = 0

	def updateData(self,datetime,data,selectedEdge):
		self.totalReturns = self.totalReturns + self.immediateReturn

		#Data Collectors
		self.priceRatios.append(data[1])
		self.zscores.append(data[2])
		self.correlations.append(data[3])
		self.momentumValues.append(data[4])
		self.priceRatioMomentums.append(data[5])

		try:
			self.returnCurve.append(self.returnCurve[-1] + self.immediateReturn)
		except:
			self.returnCurve.append(self.immediateReturn)

		if(datetime not in self.detrendedContinuousReturnCurveWithTimeIndex_MTM.keys()):
			if(self.direction == 1):
				self.continuousImmediateReturn = self.ongoingTrade.checkMTM(data['price'])
			elif(self.direction == -1):
				self.continuousImmediateReturn = self.ongoingTrade.checkMTM(data['price'])
			else:
				self.continuousImmediateReturn = 0

			self.detrendedContinuousReturnCurveWithTimeIndex_MTM[date] = self.continuousImmediateReturn
			self.continuousTotalReturns += self.continuousImmediateReturn

		try:
			self.continuousReturnCurve.append(self.continuousReturnCurve[-1] + self.continuousImmediateReturn)
		except:
			self.continuousReturnCurve.append(self.continuousImmediateReturn)

		self.continuousReturnCurveWithTimeIndex[date] = self.continuousReturnCurve[-1]
		self.detrendedContinuousReturnCurveWithTimeIndex[date] = self.immediateReturn

		if(self.immediateReturn != 0):
			self.profitDistributions[selectedEdge][0] += 1
			self.profitDistributions[selectedEdge][1] += self.immediateReturn

		if(self.positionSummary):
			row = [str(datetime), data['price'],self.direction, self.continuousReturnCurve[-1]]
			self.writePositionTransaction(row, self.positionWorksheet)

		self.immediateReturn = 0
		self.continuousImmediateReturn = 0