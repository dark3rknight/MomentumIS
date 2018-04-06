import pandas as pd
from utilities.UtilityFunctions import UtilityFunctions

class Trade:
	def __init__(self,price, direction = 1, quantity = 1, slippage = 0.1):
		exec(UtilityFunctions.initializeFunctionArguments(PairsTrade.__init__))
		self.MTMprices = {'def':price, 'daily': price, '30m':price, '5m':price}
		self.MTMasked = []

	def exitTrade(self, sellPrice):
		profit_total = (((sellPrice - self.price)*100/self.price) - self.slippage)*self.quantity
		profitMTMs = []
		for freq in self.MTMasked:
			profitMTMs.append(self.checkMTM(sellPrice, freq = freq, cutSlippage = True))
		return profit_total*self.direction, profitMTMs

	def checkMTM(self,sellPrice, freq = 'daily', cutSlippage = False):
		if(freq not in self.MTMasked):
			self.MTMasked.append(freq)
		if(freq not in self.MTMprices.keys()):
			self.MTMprices[freq] = self.price

		profit = (((sellPrice - self.MTMprices[freq])*100/self.price) - (self.slippage if cutSlippage else 0))*self.quantity
		self.MTMprices[freq] = sellPrice
		return profit*self.direction