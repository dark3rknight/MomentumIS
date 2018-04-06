import pandas as pd

class State:

	def __init__(self,name,edges,actions,finalStates, colName):
		self.name = name
		self.edges = edges
		self.actions = actions
		self.finalStates = finalStates
		self.colName = colName

	def getNextResult(self,i,toPass = None):
		selectedEdge = 'default'
		indicators = self.preRequisites(i,toPass)
		for edge in self.edges:
			if(edge == 'default'):
				continue
			else:
				flag, data = eval('self.' + edge + '(i,indicators, toPass)')
				if(flag):
					selectedEdge = edge
					break
		return selectedEdge, self.actions[edge], self.finalStates[edge],data