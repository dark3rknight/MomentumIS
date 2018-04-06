import os
import csv
import progressbar
import pandas as pd
import numpy as np
import math
from datetime import datetime,timedelta

import matplotlib.pyplot as plt
import plotly.plotly as py
import plotly.graph_objs as go
import plotly.offline

from scipy import stats
from dataPlot import *
import csv

import statistics


def sma(data, window):
    if len(data) < window:
        return 0
    return sum(data[-window:])/float(window)

def calc_ema(data, window):
    if len(data) <= 2 * window:
        return sma(data[-window:],window)
    multiplier = 2.0 / (window + 1)
    current_ema = sma(data[-window*2:-window], window)
    for value in data[-window:]:
        current_ema = (multiplier * value) + ((1 - multiplier) * current_ema)
    return current_ema

def get_all_EMAs(data, window):
    EMA = [None] * ((window))
    for i in range(window, len(data)):
        EMA.append(calc_ema(data[:i], window))
    return EMA

def smba_crossovers(pricelist, period1, period2):
    ema_period = []
    ema_period.append(period1)
    ema_period.append(period2)
    ema_period.sort()
    ema = []
    start_time = ema_period[1]
    for i in range(len(ema_period)):
        ema.append(get_all_EMAs(pricelist,ema_period[i]))
    ema1 = ema[0][1:] + [0]
    ema2 = ema[-1][1:] + [0]
    trend = []
    for i in range(len(ema[0])):
        if ema1[i] == None or ema2[i] == None:
            trend.append(0) 
        elif ema1[i] > ema2[i]:
            trend.append(1)
        elif ema1[i] < ema2[i]:
            trend.append(-1)
        else:
            trend.append(0)
    #multiAxis_LabeledPlot(pricelist,'price',ema[0],str(ema_period[0])+" ema",ema[1],str(ema_period[1])+" ema",trend,'indicator')
    return trend,ema1,ema2

def Parabolic_SAR(close, high, low, acceleration_factor, max_acceleration):
    extreme_point = [None,low[1]]
    psar = [0,high[1]]
    trend = [None,"falling"]
    accelation = [None,acceleration_factor]
    change = [None,accelation[1]*(psar[1] - extreme_point[1])]
    initial_psar = [None,None]
    for i in range(2,len(close)):
        if trend[i-1] == "falling":
            ipsar = max(high[i-1],high[i-2],(psar[i-1]-change[i-1]))
        elif trend[i-1] == "rising":
            ipsar = min(low[i-1],low[i-2],(psar[i-1]-change[i-1]))
        initial_psar.append(ipsar)
        if trend[i-1] == "falling":
            if (initial_psar[i] > high[i]):
                newpsar = initial_psar[i]
            else:
                newpsar = extreme_point[i-1]
        if trend[i-1] == "rising":
            if (initial_psar[i] < low[i]):
                newpsar = initial_psar[i]
            else:
                newpsar = extreme_point[i-1]
        psar.append(newpsar)
        if psar[i] > close[i]:
            trend.append("falling")
        else:
            trend.append("rising")
        if trend[i] == "falling":
            extreme_point.append(min(extreme_point[i-1],low[i]))
        else:
            extreme_point.append(max(extreme_point[i-1],high[i]))
        if trend[i] == trend[i-1]:
            if (extreme_point[i] != extreme_point[i-1]) and  (accelation[i-1] < max_acceleration):
                new_acc = accelation[i-1] + acceleration_factor
            else:
                new_acc = accelation[i-1]
        else:
            new_acc = acceleration_factor
        accelation.append(new_acc)
        change.append(accelation[i]*(psar[i]-extreme_point[i]))
    #multiplePlots(close,'price',psar,'PSAR')
    trend_1 = []
    for i in range(len(trend)):
        if trend[i] == 'rising':
            trend_1.append(1)
        elif trend[i] == 'falling':
            trend_1.append(-1)
        else:
            trend_1.append(0)

    return psar,trend_1


def is_number(s):
    try:
        int(s)
        return True
    except:
        return False

def OLS_Slope(pricelist, period):
    OLS_Slope = [0]*(period)
    for i in range(period,len(pricelist)):
        time_variable = list(range(period))
        OLS_Slope.append(stats.linregress(time_variable,pricelist[i-period:i]).slope)
    OLS_Slope = [1:]+[0]
    #multi_subPlot(pricelist,'price',OLS_Slope,'OLS_Slope')
    retslope = []
    for i in range(len(OLS_Slope)):
        if OLS_Slope[i] > 0:
            retslope.append(1)
        else:
            retslope.append(-1)
    return retslope,OLS_Slope
