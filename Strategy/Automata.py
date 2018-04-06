import sys
sys.path.append('/home/ishan/Desktop/Ishan/Stock Data/Code Files/Strategy')
import pandas as pd
import numpy as np
from utilities.UtilityFunctions import UtilityFunctions

class Automata:
	def __init__(self,startState, states,edges, actions, finalStates):
		exec(UtilityFunctions.initializeFunctionArguments(Automata.__init__))
		self.currentState = startState

	def __init__(self,automataCSV):
		automataDf = pd.read_csv(automataCSV)
		self.currentState = automataDf[automataDf['state'] == 'start']['finalState'].values[0]
		self.states = np.delete(automataDf.state.unique(),0)
		self.edges = {}
		self.actions = {}
		self.finalStates = {}
		for state in self.states:
			automataStateSpecificDf = automataDf[automataDf['state'] == state]
			self.edges[state] = list(automataStateSpecificDf.edge)
			self.actions[state] = {}
			self.finalStates[state] = {}
			for edge in self.edges[state]:
				automataStateAndEdgeSpecificDf = automataStateSpecificDf[automataStateSpecificDf['edge'] == edge]
				self.actions[state][edge] = automataStateAndEdgeSpecificDf.action.values[0]
				self.finalStates[state][edge] = automataStateAndEdgeSpecificDf.finalState.values[0]

	def initalizeStates(self,stockdf, colName, stateInitializers):
		self.stockdf = stockdf
		for state in self.states:
			exec('from states.' + state + ' import ' + state)
			exec('self.' + state + ' = ' + state + '(stockdf,state,edges,actions,finalStates,colName, stateInitializers[state])')

	def generateDecision(self,stockdf, colName, stateInitializers, startPoint):
		self.initalizeStates(stockdf, colName, stateInitializers)
		for i in range(startPoint,stockdf.shape[0]):
			selectedEdge, action, self.currentState, inf = eval('self.' + self.currentState + '.getNextResult(i,inf)')
			yield selectedEdge, action, self.currentState, inf
