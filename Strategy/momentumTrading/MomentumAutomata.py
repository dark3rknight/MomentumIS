import sys
import os
currentDir = os.getcwd()
sys.path.append(currentDir + '/Strategy')
sys.path.append(currentDir)
sys.path.append(currentDir + '/Strategy/momentumTrading')
from Automata import Automata
import pandas as pd
import utilities.momentumIndicators as mi

class MomentumAutomata(Automata):
	def __init__(self,startState, states,edges, actions, finalStates, parameters):
		Automata.__init__(self,startState,states,edges.actions,finalStates)
		self.parameters = parameters

	def __init__(self,parameters):
		self.automataCSV = parameters['automataFile']
		Automata.__init__(self,self.automataCSV)
		self.parameters = parameters

	def initializeStates(self,stateConstants, stockdf):
		self.index = None
		self.toPass = None
		self.inTrade = False
		self.entryTime = None
		self.direction = 0
		self.stopLossLimit = None
		self.cPCount = 0
		self.high = None
		indicators = self.generateIndicators(stateConstants, stockdf)
		for state in self.states:
			exec('from states.' + state + ' import ' + state)
			exec('self.' + state + ' = ' + state + '(state,self.edges[state],self.actions[state],self.finalStates[state],stateConstants, indicators)')

	def generateIndicators(self,stateConstants, stockdf):
		smba = mi.smba_crossovers(stockdf[stateConstants['PriceColumn']], stateConstants['smba_period1'], stateConstants['smba_period2'])
		psar = mi.Parabolic_SAR(stockdf[stateConstants['PriceColumn']], stockdf[stateConstants['HighColumn']], stockdf[stateConstants['LowColumn']],stateConstants['psar_AF'], stateConstants['psar_MA'])
		ols = mi.OLS_Slope(stockdf[stateConstants['PriceColumn']], stateConstants['ols_period'])
		indicators = [smba, psar, ols]
		indicators = pd.DataFrame()
		indicators['PSAR_Indicator'] = pd.Series(psar[0])
		indicators['PSAR_Val'] = pd.Series(psar[1])
		indicators['SMBA_Indicator'] = pd.Series(smba[0])
		indicators['SMBA_period1'] = pd.Series(smba[1])
		indicators['SMBA_period2'] = pd.Series(smba[2])
		indicators['OLS_Indicator'] = pd.Series(ols[0])
		indicators['OLS_Val'] = pd.Series(ols[1])
		indicators.index = stockdf.index
		return indicators

	def generateDecision(self, timestamp, prices):
		selectedEdge, action, self.currentState, data, row = eval('self.' + self.currentState + '.getNextResult(prices, timestamp,self.toPass)')
		if(action == 'enterMarket'):
			self.inTrade = True
			self.direction = data['Direction']
			self.entryTime = timestamp
		elif(action == 'exitMarket'):
			self.inTrade = False
			self.entryTime = None
			self.direction = 0
			self.stopLossLimit = None
			self.high = None
		if(self.inTrade):
			if(self.high is not None):
				if(self.direction*(prices.ix[0]['HIGH'] if (self.direction == 1) else prices.ix[0]['LOW']) > self.direction*self.high):
					self.high = (prices.ix[0]['HIGH'] if (self.direction == 1) else prices.ix[0]['LOW'])
			else:
				self.high = prices.ix[0]['HIGH']
			self.stopLossLimit = self.high*(1 - self.direction*(self.parameters['stopLoss']/100))
		self.toPass = {'Direction': self.direction, 'Entry Time': self.entryTime, 'stopLossLimit': self.stopLossLimit}
		return selectedEdge, action, self.currentState, data, row