import sys
sys.path.append('/home/ishan/Desktop/Ishan/Stock Data/Code Files')
sys.path.append('/home/ishan/Desktop/Ishan/Stock Data')

import numpy as np
import scipy.stats as stats
import xlsxwriter
import pandas as pd
import math
from Trade import Trade
from Automata import Automata
from datetime import datetime
from utilities.UtilityFunctions import UtilityFunctions
from utilities.FinancialFunctions import FinancialFunctions

class Strategy:	
	def __init__(self, transactionSummary, positionSummary, automataFile, parameters = None):
		exec(UtilityFunctions.initializeFunctionArguments(Strategy.__init__))
		self.colName = parameters['colName']
		self.returnCurve = []
		self.continuousReturnCurve = []
		self.continuousReturnCurveWithTimeIndex = {}
		self.detrendedContinuousReturnCurveWithTimeIndex = {}
		self.detrendedContinuousReturnCurveWithTimeIndex_MTM = {}
		self.equityCurve = []
		self.equityCurveWithTimeIndex = {}
		self.returnListWithTime = []
		self.returnListWithIndex = []
		self.returns = []
		self.totalReturns = 0
		self.continuousTotalReturns = 0
		self.immediateReturn = 0
		self.profitDistributions = {}
		self.onGoingTrade = None
		self.direction = 0
		if(automataFile):
			self.automata = Automata(automataFile)
		if(transactionSummary):
			headRow = ['Start Time','End Time','Start Index', 'End Index','Buy Price','Sell Price','Direction','Profit']
			self.workbook, self.worksheet, self.formatRed = self.createTransactionFile(transactionSummary, headRow, sheetName)
			self.tsRowNumber = 2
		else:
			self.workbook, self.worksheet, self.formatRed = [None,None,None]

		if(positionSummary):
			headRow = ['Datetime', 'Close','Position']
			self.positionWorkbook, self.positionWorksheet, self.positionFormatRed = self.createTransactionFile(positionSummary, headRow, sheetName)
			self.psRowNumber = 2
		else:
			self.positionWorkbook, self.positionWorksheet, self.positionFormatRed = [None,None,None]

	def createTransactionFile(self, filename, headRow, sheetName = 'Sheet1'):
		workbook = xlsxwriter.Workbook(filename)
		formatRed = workbook.add_format()
		formatRed.set_bg_color('red')
		worksheet = workbook.add_worksheet(sheetName)
		worksheet.write_row('A1', headRow)
		return workbook,worksheet, formatRed

	def writeTransaction(self,profit,row,worksheet, formatRed):
		if(profit > 0):
			worksheet.write_row('A' + str(self.tsRowNumber), row)
		else:
			worksheet.write_row('A' + str(self.tsRowNumber), row, formatRed)
		self.tsRowNumber += 1

	def writePositionTransaction(self,row,worksheet):
		worksheet.write_row('A' + str(self.psRowNumber), row)
		self.psRowNumber += 1

	def testStrategy(self,stockdf, stockName = None, startDate = None, endDate = None):
		self.stockName = stockName
		self.stockdf = stockdf
		self.stockdf_datetime = stockdf.reset_index()
		stateInitializers = {}
		self.automata.initializeStates(stockdf, self.colName, stateInitializers)
		for i,selectedEdge,action,currentState,inf in self.automata.executeSequence(stockdf):
			exec('self.' + action + '(i,inf,selectedEdge)')

	def closingFormalities(self):
		#Calculate drawdown and sharpe ratio
		self.maxDrawdown_continuous = FinancialFunctions.maxDrawdown(self.continuousReturnCurve)
		self.maxDrawdown_onclosedTrades = FinancialFunctions.maxDrawdown(self.returnCurve)
		self.sharpeRatio_continuous = FinancialFunctions.sharpeRatio(self.continuousReturnCurve, numberOfDailyCandles = self.parameters['numberOfDailyCandles'])
		self.sharpeRatio_onclosedTrades = FinancialFunctions.sharpeRatio(self.returnCurve, numberOfDailyCandles = self.parameters['numberOfDailyCandles'])
		self.totalNumberOfTrades = len(self.returns)
		if(self.workbook):
			self.workbook.close()
		if(self.positionWorkbook):
			self.positionWorkbook.close()
		print(self.totalReturns, self.continuousTotalReturns)
		return self.totalReturns