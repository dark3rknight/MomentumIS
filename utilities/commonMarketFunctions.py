import os
import scipy.stats as stats
from datetime import datetime
import pandas as pd

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
