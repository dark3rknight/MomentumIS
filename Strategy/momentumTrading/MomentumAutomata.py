import sys
sys.path.append('/home/ishan/Desktop/Ishan/Stock Data/Code Files/Strategy')
sys.path.append('/home/ishan/Desktop/Ishan/Stock Data/Code Files/Strategy/pairsTrading')
from Automata import Automata
import pandas as pd

class PairsAutomata(Automata):
	def __init__(self,startState, states,edges, actions, finalStates):
		Automata.__init__(self,startState,states,edges.actions,finalStates)

	def __init__(self,automataCSV):
		Automata.__init__(self,automataCSV)

	def initializeStates(self,stateConstants):
		self.index = None
		self.toPass = None
		self.inTrade = False
		self.entryTime = None
		self.direction = 0
		self.cPCount = 0
		for state in self.states:
			exec('from states.' + state + ' import ' + state)
			exec('self.' + state + ' = ' + state + '(state,self.edges[state],self.actions[state],self.finalStates[state],stateConstants)')

	def initializeDataFrames(self, numberOfFrames, columns):
		self.stock1dfs = []
		self.stock2dfs = []
		for i in range(numberOfFrames):
			stock1df = pd.DataFrame(columns = columns)
			stock2df = pd.DataFrame(columns = columns)
			self.stock1dfs.append(stock1df)
			self.stock2dfs.append(stock2df)

	def generateDecision(self,data1, data2):
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