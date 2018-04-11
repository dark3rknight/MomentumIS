import os
import scipy.stats as stats
from datetime import datetime
import pandas as pd
import inspect

def makeDir(name):
	if(not os.path.isdir(name)):
		os.mkdir(name)
	return name

def correlation(wave1, wave2, gaps = False):
	if(gaps):
		newWave1 = []
		newWave2 = []
		if(len(wave1) != len(wave2)):
			raise Exception('Length not similar')
		else:
			for i in range(len(wave1)):
				if(wave1[i] != '-')and(wave2[i] != '-'):
					newWave1.append(wave1[i])
					newWave2.append(wave2[i])

		return stats.pearsonr(newWave1,newWave2)[0], len(newWave1)
	else:
		size = min(len(wave1), len(wave2))
		return stats.pearsonr(wave1[:size], wave2[:size])[0], size

def getFunctionArguments(f):
	sign = inspect.signature(f)
	sign = str(sign)
	sign = sign[1:-1]
	sign = sign.split(',')
	return sign


def matchTime(time,string,format = '%H:%M'):
	return time.time() == datetime.strptime(string,format).time()

def matchDate(date,string,format = '%d/%m/%Y'):
	return date.date() == datetime.strptime(string,format).date()

def isWeekend(date):
	if(date.weekday() > 4):
		return True
	else:
		return False

def isMarketCloseTime(time):
	return (time.time() > datetime.strptime('15:30','%H:%M').time()) or (time.time() < datetime.strptime('09:15','%H:%M').time())

def isMarketClosed_DayEnd(time):
	return (time.time() > datetime.strptime('15:30','%H:%M').time())

def isMarketNotOpenYet(time):
	return (time.time() < datetime.strptime('09:15','%H:%M').time())

def isMarketClosedForTheDay(prices,timestamp):
	return (prices[(prices.index >= timestamp) & (prices.index <= timestamp + pd.Timedelta(hours = 6, minutes = 15))].shape[0] == 0)

def howManyPointsInTheMarketForTheDay(prices,timestamp):
	return prices[(prices.index >= timestamp) & (prices.index <= timestamp + pd.Timedelta(hours = 6, minutes = 15))].shape[0]

def arangeNumbers(start,end,step):
	return np.linspace(start,end, num = round((end - start)/step), endpoint = False)