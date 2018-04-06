import sys
sys.path.append('/home/ishan/Desktop/Ishan/Stock Data/Code Files')
sys.path.append('/home/ishan/Desktop/Ishan/Stock Data')

import numpy as np
import scipy.stats as stats
import xlsxwriter
import pandas as pd
import math

class FinancialFunctions:
	def sharpeRatio(returnCurve, timeFrame = 'daily', numberOfDailyCandles = 1, riskFreeReturn = 0):
		returns = []
		numberOfCandlesToTake = {'annual': numberOfDailyCandles*21*12 , 'monthly': numberOfDailyCandles*21, 'daily': numberOfDailyCandles, 'hourly': numberOfDailyCandles/6}
		for i in range(1,len(returnCurve)):
			returns.append(returnCurve[i] - returnCurve[i-1])
		prev_i = 0
		newReturns = []
		for i in range(numberOfCandlesToTake[timeFrame],len(returnCurve), numberOfCandlesToTake[timeFrame]):
			newReturns.append(np.sum(returns[prev_i: i]))
			prev_i = i

		averageReturn = np.mean(newReturns)
		standardDeviation = np.std(newReturns)

		sharpeRatio = ((averageReturn - riskFreeReturn)*math.sqrt(len(newReturns)))/(standardDeviation)
		return sharpeRatio

	def maxDrawdown(returnCurve):
		peakPoint = 0
		drawDown = 0
		for i in returnCurve:
			if(i > peakPoint):
				peakPoint = i
			else:
				if((peakPoint - i) > drawDown):
					drawDown = peakPoint - i
		return drawDown