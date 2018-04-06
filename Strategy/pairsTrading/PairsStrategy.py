import pandas as pd
import numpy as np
from Strategy import Strategy
from datetime import datetime
from pairsTrading.PairsAutomata import PairsAutomata
from pairsTrading.PairsTrade import PairsTrade
from utilities.UtilityFunctions import UtilityFunctions
import progressbar
from datetime import timedelta, time, date

class PairsStrategy(Strategy):
	def __init__(self, parameters = None):
		Strategy.__init__(self, None, None,None, parameters = parameters)
		exec(UtilityFunctions.initializeFunctionArguments(PairsStrategy.__init__))
		defaultparameters = {'zscoreBuy':2, 'zscoreSell':0, 'zscoreStopLoss':3.5, 'correlationSelectionThreshold':0.3, 'stopLossFlag':True, 'correlationCheckFlag':True, 'pastWindow':40, 'momentumCheck':False, 'momentumWindow':40, 'momentumThresholds':[20,80],'momentumCheckWaitWindow':10, 'almostRevertedFlag':False, 'zscoreAlmostMeanReverted':0.1, 'colName': 'EQUITY', 'numberOfDailyCandles': 1, 'automataFile': './pairsTrading/pairsTrading_automata.csv', 'transactionSummary': None, 'positionSummary': None}
		self.parameters = UtilityFunctions.fillDefaultData(parameters, defaultparameters)

		#Constatnts
		self.colName = self.parameters['colName']
		self.pastWindow = self.parameters['pastWindow']
		self.momentumWindow = self.parameters['momentumWindow']
		self.automata = PairsAutomata(self.parameters['automataFile'])
		self.numberOfDailyCandles = self.parameters['numberOfDailyCandles']
		self.transactionSummary = self.parameters['transactionSummary']
		self.positionSummary = self.parameters['positionSummary']
		self.offset = max(self.pastWindow, self.momentumWindow, self.parameters['pastWindow_std'])
		self.parameters['offset'] = self.offset
		self.predictiveModelDataRow = None
		self.positionsWithTimeIndex = {}
		self.MTMReturn_30m = 0
		self.MTMWithTimeIndex = {}
		self.toWriteStock1Prices = {}
		self.toWriteStock2Prices = {}

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
			headRow = ['Start Time','End Time','Stock 1','Buy Price','Sell Price','Stock 2','Short Sell Price','Buy Back Price','Profit']
			self.workbook, self.worksheet, self.formatRed = self.createTransactionFile(self.transactionSummary, headRow, sheetName)
			self.tsRowNumber = 2
		else:
			self.workbook, self.worksheet, self.formatRed = [None,None,None]


		if(self.positionSummary):
			headRow = ['Datetime', 'Close 1','Close 2','Position 1','Position 2', 'Zscore', 'Return Curve']
			self.positionWorkbook, self.positionWorksheet, self.positionFormatRed = self.createTransactionFile(self.positionSummary, headRow, sheetName)
			self.psRowNumber = 2
		else:
			self.positionWorkbook, self.positionWorksheet, self.positionFormatRed = [None,None,None]

	def testStrategy(self,stock1dfs,stock2dfs, stockName1 = None, stockName2 = None, startDate = None, endDate = None):
		print(self.parameters['pastWindow'], self.parameters['zscoreBuy'], self.parameters['zscoreSell'])
		stock1df,stock2df = UtilityFunctions.selectData(stock1dfs[0],stock2dfs[0],startDate,endDate, self.offset)
		stock1df_30m,stock2df_30m = UtilityFunctions.selectData(stock1dfs[1], stock2dfs[1], startDate, endDate, self.offset)
		stock1dfs = [stock1df, stock1df_30m]
		stock2dfs = [stock2df, stock2df_30m]
		self.stock1dfs = stock1dfs
		self.stock2dfs = stock2dfs
		self.stockName1 = stockName1
		self.stockName2 = stockName2
		self.automata.initializeStates(self.parameters)
		self.automata.initializeDataFrames(len(stock1dfs), stock1dfs[0].columns)
		bar = progressbar.ProgressBar()
		startDate = np.min(stock1dfs[0].DATE)
		endDate = np.max(stock2dfs[0].DATE)
		print(startDate, endDate)
		for date in bar(UtilityFunctions.daterange(startDate, endDate + timedelta(days = 1))):
			self.positionUpdateDone = False
			data1 = UtilityFunctions.getData_Date(stock1dfs, date)
			data2 = UtilityFunctions.getData_Date(stock2dfs, date)
			if(len(data1[0]) == 0)or(len(data2[0]) == 0):
				continue
			selectedEdge,action,currentState,data, row = self.automata.generateDecision(data1,data2)
			self.predictiveModelDataRow = row
			# if(date == endDate) and (currentState != 'outOfMarket'):
			# 	action = 'exitMarket'
			# 	selectedEdge = 'residue'
			if(action != 'continue'):
				exec('self.' + action + '(date,data,selectedEdge)')
			if(data != None):
				self.updateData(date,data,selectedEdge)
		return self.closingFormalities()

	def exitAndEnterMarket(self,date,data,selectedEdge):
		self.exitMarket(date,data,selectedEdge)
		self.enterMarket(date,data,selectedEdge)

	def enterMarket(self,date,data,selectedEdge):
		self.direction = data[0]
		if(self.direction == 1):
			self.boughtStock = self.stockName2
			self.soldStock = self.stockName1
			self.buyPrice = data[6][1]
			self.buyQuantity = data[7][1]
			self.sellPrice = data[6][0]
			self.sellQuantity = data[7][0]
		else:
			self.boughtStock = self.stockName1
			self.soldStock = self.stockName2
			self.buyPrice = data[6][0]
			self.buyQuantity = data[7][0]
			self.sellPrice = data[6][1]
			self.sellQuantity = data[7][1]

		if(self.parameters['useUnevenLots']):
			self.ongoingTrade = PairsTrade(self.buyPrice, self.sellPrice, self.buyQuantity, self.sellQuantity)
		else:
			self.ongoingTrade = PairsTrade(self.buyPrice, self.sellPrice)
		self.entryTime = date
		if(not self.positionUpdateDone):
			for tm in UtilityFunctions.timerange(time(9,30), time(15,30), timedelta(minutes = 30)):
				if(tm < time(15,30)):
					self.positionsWithTimeIndex[datetime.combine(date, tm)] = 0
					self.MTMWithTimeIndex[datetime.combine(date,tm)] = self.MTMReturn_30m
				else:
					self.positionsWithTimeIndex[datetime.combine(date, tm)] = -self.direction
					self.MTMWithTimeIndex[datetime.combine(date,tm)] = self.MTMReturn_30m
		else:
			for tm in UtilityFunctions.timerange(time(9,30), time(15,30), timedelta(minutes = 30)):
				if(time == time(15,30)):
					self.positionsWithTimeIndex[datetime.combine(date, tm)] = -self.direction
		self.positionUpdateDone = True

	def exitMarket(self,date,data = None,selectedEdge = None):
		errorFlag = False
		if(self.direction == 1):
			self.buyBackPrice = data[6][0]
			self.sellBackPrice = data[6][1]
		else:
			self.buyBackPrice = data[6][1]
			self.sellBackPrice = data[6][0]

		try:
			self.exitTime_30m = datetime.strptime(data[7][0],'%H:%M:%S').time()
		except IndexError:
			self.exitTime_30m = False
		except TypeError:
			self.exitTime_30m = False

		if(selectedEdge == 'stockHasMissingData'):
			self.MTMWithTimeIndex[max(self.MTMWithTimeIndex.keys())] -= 0.1
			self.MTMReturn_30m = self.MTMWithTimeIndex[max(self.MTMWithTimeIndex.keys())]
			for tm in UtilityFunctions.timerange(time(9,30), time(15,30), timedelta(minutes = 30)):
				self.positionsWithTimeIndex[datetime.combine(date, tm)] = 0
				self.MTMWithTimeIndex[datetime.combine(date,tm)] = self.MTMReturn_30m
		else:
			for tm in UtilityFunctions.timerange(time(9,30), time(15,30), timedelta(minutes = 30)):
				if(self.exitTime_30m):
					if(tm < self.exitTime_30m):
						self.positionsWithTimeIndex[datetime.combine(date, tm)] = -self.direction
						if(self.direction == 1):
							self.MTMReturn_30m = self.MTMReturn_30m + self.ongoingTrade.checkDailyMTM_30m(self.stock1dfs[1][self.stock1dfs[1].index == datetime.combine(date,tm)][self.colName], self.stock2dfs[1][self.stock2dfs[1].index == datetime.combine(date,tm)][self.colName])
						else:
							self.MTMReturn_30m = self.MTMReturn_30m + self.ongoingTrade.checkDailyMTM_30m(self.stock2dfs[1][self.stock2dfs[1].index == datetime.combine(date,tm)][self.colName], self.stock1dfs[1][self.stock1dfs[1].index == datetime.combine(date,tm)][self.colName])
						self.MTMWithTimeIndex[datetime.combine(date,tm)] = self.MTMReturn_30m
					elif(tm == self.exitTime_30m):
						self.positionsWithTimeIndex[datetime.combine(date, tm)] = -self.direction
						if(self.direction == 1):
							self.MTMReturn_30m = self.MTMReturn_30m + self.ongoingTrade.checkDailyMTM_30m(self.stock1dfs[1][self.stock1dfs[1].index == datetime.combine(date,tm)][self.colName], self.stock2dfs[1][self.stock2dfs[1].index == datetime.combine(date,tm)][self.colName], cutSlippage = True)
						else:
							self.MTMReturn_30m = self.MTMReturn_30m + self.ongoingTrade.checkDailyMTM_30m(self.stock2dfs[1][self.stock2dfs[1].index == datetime.combine(date,tm)][self.colName], self.stock1dfs[1][self.stock1dfs[1].index == datetime.combine(date,tm)][self.colName], cutSlippage = True)
						self.MTMWithTimeIndex[datetime.combine(date,tm)] = self.MTMReturn_30m					
					else:
						self.positionsWithTimeIndex[datetime.combine(date, tm)] = 0
						self.MTMWithTimeIndex[datetime.combine(date,tm)] = self.MTMReturn_30m

				else:
					self.positionsWithTimeIndex[datetime.combine(date, tm)] = -self.direction
					if(self.direction == 1):
						self.MTMReturn_30m = self.MTMReturn_30m + self.ongoingTrade.checkDailyMTM_30m(self.stock1dfs[1][self.stock1dfs[1].index == datetime.combine(date,tm)][self.colName], self.stock2dfs[1][self.stock2dfs[1].index == datetime.combine(date,tm)][self.colName], cutSlippage = (tm == time(15,30)))
					else:
						self.MTMReturn_30m = self.MTMReturn_30m + self.ongoingTrade.checkDailyMTM_30m(self.stock2dfs[1][self.stock2dfs[1].index == datetime.combine(date,tm)][self.colName], self.stock1dfs[1][self.stock1dfs[1].index == datetime.combine(date,tm)][self.colName], cutSlippage = (tm == time(15,30)))
					self.MTMWithTimeIndex[datetime.combine(date,tm)] = self.MTMReturn_30m

		try:
			profitMTM, profit = self.ongoingTrade.exitTrade(self.buyBackPrice, self.sellBackPrice)
			self.detrendedContinuousReturnCurveWithTimeIndex_MTM[date] = profitMTM
			self.continuousImmediateReturn = profitMTM
			self.continuousTotalReturns += profitMTM
		except AttributeError:
			print('Inspect here', self.stockName1, self.stockName2, date)
			profit = 0
			errorFlag = True

		self.exitTime = date
		self.immediateReturn = profit
		self.returns.append(self.immediateReturn)

		if(self.workbook):
			row = [str(self.entryTime), str(self.exitTime), self.boughtStock, '%.3f' % self.buyPrice, '%.3f' % self.sellBackPrice, self.soldStock, '%.3f' % self.sellPrice, '%.3f' % self.buyBackPrice, '%.3f' % profit]
			self.writeTransaction(profit, row, self.worksheet, self.formatRed)

		if(self.predictiveModelDataRow and (not errorFlag)):
			for cP, row in self.predictiveModelDataRow.items():
				newRow = [(self.exitTime - self.entryTime).days] + row + [profit, (1 if (profit > 0) else 0),(1 if ((profit - row[-5]) > 0) else 0)]
				self.parameters['predictiveModel'].add(newRow, cP)
			self.predictiveModelDataRow = None

		self.ongoingTrade = None
		self.buyPrice = None
		self.sellPrice = None
		self.buyBackPrice = None
		self.sellBackPrice = None
		self.returnListWithTime.append([profit,self.entryTime, self.exitTime, self.direction])

		self.positionUpdateDone = True
		self.direction = 0

	def updateData(self,date,data,selectedEdge):
		self.totalReturns = self.totalReturns + self.immediateReturn
		self.priceRatios.append(data[1])
		self.zscores.append(data[2])
		self.correlations.append(data[3])
		self.momentumValues.append(data[4])
		self.priceRatioMomentums.append(data[5])
		try:
			self.returnCurve.append(self.returnCurve[-1] + self.immediateReturn)
		except:
			self.returnCurve.append(self.immediateReturn)

		if(date not in self.detrendedContinuousReturnCurveWithTimeIndex_MTM.keys()):
			if(self.direction == 1):
				self.continuousImmediateReturn = self.ongoingTrade.checkDailyMTM(data[6][0], data[6][1])
			elif(self.direction == -1):
				self.continuousImmediateReturn = self.ongoingTrade.checkDailyMTM(data[6][1], data[6][0])
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
			row = [str(date), data[6][0],data[6][1],-self.direction,self.direction, inf[2], self.continuousReturnCurve[-1]]
			self.writePositionTransaction(row, self.positionWorksheet)
		if(not self.positionUpdateDone):
			for tm in UtilityFunctions.timerange(time(9,30), time(15,30), timedelta(minutes = 30)):
				self.positionsWithTimeIndex[datetime.combine(date, tm)] = -self.direction
				if(self.direction == 1):
					self.MTMReturn_30m = self.MTMReturn_30m + self.ongoingTrade.checkDailyMTM_30m(self.stock1dfs[1][self.stock1dfs[1].index == datetime.combine(date,tm)][self.colName], self.stock2dfs[1][self.stock2dfs[1].index == datetime.combine(date,tm)][self.colName])
				elif(self.direction == -1):
					self.MTMReturn_30m = self.MTMReturn_30m + self.ongoingTrade.checkDailyMTM_30m(self.stock2dfs[1][self.stock2dfs[1].index == datetime.combine(date,tm)][self.colName], self.stock1dfs[1][self.stock1dfs[1].index == datetime.combine(date,tm)][self.colName])
				self.MTMWithTimeIndex[datetime.combine(date,tm)] = self.MTMReturn_30m
		self.immediateReturn = 0
		self.continuousImmediateReturn = 0