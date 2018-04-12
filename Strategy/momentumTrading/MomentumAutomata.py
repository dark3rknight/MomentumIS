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
	def __init__(self,automataCSV):
		Automata.__init__(self,automataCSV)

	def initializeStates(self,stateConstants, stockdf):
		self.index = None
		self.toPass = None
		self.inTrade = False
		self.entryTime = None
		self.direction = 0
		self.cPCount = 0
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

	def generateDecision(self, data):
		for i in range(len(self.stock1dfs)):
			self.stock1dfs[i] = pd.concat([self.stock1dfs[i], data1[i]])

		for i in range(len(self.stock2dfs)):
			self.stock2dfs[i] = pd.concat([self.stock2dfs[i], data2[i]])

		selectedEdge, action, self.currentState, data, row = eval('self.' + self.currentState + '.getNextResult(self.stock1dfs, self.stock2dfs,self.toPass)')
		if(action == 'enterMarket'):
			self.inTrade = True
			self.direction = data[0]
			self.entryTime = self.stock1dfs[0].iloc[-1].DATE
		elif(action == 'exitMarket'):
			self.inTrade = False
			self.entryTime = None
			self.direction = 0
		self.toPass = [self.direction, self.entryTime]
		return selectedEdge, action, self.currentState, data, row