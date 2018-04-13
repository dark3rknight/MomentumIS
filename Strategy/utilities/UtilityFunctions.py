import math
import numpy as np
import inspect
from datetime import timedelta, date, datetime, time
from pandas.tseries.offsets import BDay
import os

class UtilityFunctions:
	def fillDefaultData(inputData, defaultData):
		if(inputData == None):
			return defaultData
		else:
			for key,value in defaultData.items():
				if(key not in inputData.keys()):
					inputData[key] = value
				else:
					continue
			return inputData

	def initializeFunctionArguments(f):
		sign = inspect.signature(f)
		sign = str(sign)
		sign = sign[1:-1]
		sign = sign.split(',')
		if(sign[0] == 'self'):
			sign = sign[1:]
		execString = ''
		for arg in sign:
			if(arg.find('=') == -1):
				execString += 'self.' + arg.strip() + ' = ' + arg.strip() + '\n'
			else:
				arg = arg.split('=')
				execString += 'self.' + arg[0].strip() + ' = ' + arg[0].strip() + '\n'
		return execString[:-1]

	def makeDir(path, offset = './'):
		origPath = path
		if(path[:2] == './'):
			path = path[2:]
		firstDirPos = path.find('/')
		if(firstDirPos == -1):
			if(not os.path.isdir(offset + path)):
				os.mkdir(offset + path)
			return origPath
		else:
			firstDir = path[:firstDirPos]
			if(not os.path.isdir(offset + '/' + firstDir)):
				os.mkdir(offset + '/' + firstDir)
			UtilityFunctions.makeDir(path[firstDirPos + 1:], offset = offset + path[:firstDirPos] + '/')
			return origPath

	def selectData(stock1, stock2, tradeStartDate = None, tradeEndDate = None, pastDataWindow = 0):
		OverLappingIndices = stock1.index.intersection(stock2.index)
		prices1 = stock1.ix[OverLappingIndices]
		prices2 = stock2.ix[OverLappingIndices]
		if(tradeStartDate is not None):
			startDate = datetime.strptime(tradeStartDate, '%d/%m/%Y') - BDay(pastDataWindow)
			endDate = datetime.strptime(tradeEndDate, '%d/%m/%Y')
			prices1 = prices1[(prices1.index >= startDate) & (prices1.index <= endDate)]
			prices2 = prices2[(prices2.index >= startDate) & (prices2.index <= endDate)]
		return prices1, prices2

	def selectData_OnDate(stockdf, tradeStartDate = None, tradeEndDate = None, pastDataWindow = 0):
		if(tradeStartDate is not None):
			startDate = datetime.strptime(tradeStartDate, '%d/%m/%Y') - BDay(pastDataWindow)
			endDate = datetime.strptime(tradeEndDate, '%d/%m/%Y')
			stockdf = stockdf[(stockdf.index >= startDate) & (stockdf.index <= endDate)]
		return stockdf

	def selectData_notDaily(stock1, stock2, tradeStartDate = None, tradeEndDate = None, pastDataWindow = 0, numberOfCandlesPerDay = 1):
		OverLappingIndices = stock1.index.intersection(stock2.index)
		prices1 = stock1.ix[OverLappingIndices]
		prices2 = stock2.ix[OverLappingIndices]
		if(tradeStartDate is not None):
			startDate = datetime.strptime(tradeStartDate, '%d/%m/%Y')
			endDate = datetime.strptime(tradeEndDate, '%d/%m/%Y')
			prices1 = prices1[(prices1.index >= startDate) & (prices1.index <= endDate)]
			prices2 = prices2[(prices2.index >= startDate) & (prices2.index <= endDate)]
		return prices1, prices2

	def getData_Date(stockdfs, date):
		returnDfs = []
		for stockdf in stockdfs:
			returnDf = stockdf[stockdf.DATE == date]
			returnDfs.append(returnDf)
		return returnDfs

	def datetimerange(start_date, end_date, start_time = '09:30', end_time = '15:30', timedel = 'minutes = 30', feededDatetime = True):
		if(not feededDatetime):
		    start_time = datetime.strptime(start_time, '%H:%M').time()
		    end_time = datetime.strptime(end_time, '%H:%M').time()
		    start_date = datetime.combine(start_date, start_time)
		    end_date = datetime.combine(end_date, end_time)

		counter = start_date
		while(counter <= end_date):
			yield counter
			counter = eval('counter + timedelta(' + timedel + ')') 

	def daterange(start_date, end_date):
	    for n in range(int ((end_date - start_date).days)):
	        yield start_date + timedelta(n)

	def timerange(startTime, endTime, delta):
	    currentTime = startTime
	    while(currentTime <= endTime):
	        yield currentTime
	        currentTime = (datetime.combine(date.today(), currentTime) + delta).time()
	
	def arangeNumbers(start,end,step):
		return np.linspace(start,end, num = round((end - start)/step), endpoint = False)