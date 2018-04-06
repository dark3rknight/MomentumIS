import pandas as pd
from Trade import Trade
from utilities.UtilityFunctions import UtilityFunctions

class PairsTrade(Trade):
	def __init__(self,buyPrice, sellPrice, buyQuantity = 1, sellQuantity = 1,slippage = 0.1):
		exec(UtilityFunctions.initializeFunctionArguments(PairsTrade.__init__))
		self.longMTMprice = buyPrice
		self.shortMTMprice = sellPrice
		self.longMTMprice_30m = buyPrice
		self.shortMTMprice_30m = sellPrice
		self.buyQuantity = buyQuantity/(buyQuantity + sellQuantity)
		self.sellQuantity = sellQuantity/(buyQuantity + sellQuantity)

	def exitTrade(self, buyBackPrice, sellBackPrice):
		profit1 = (((sellBackPrice - self.longMTMprice)*100/self.buyPrice) - self.slippage)*self.buyQuantity
		profit2 = (((self.shortMTMprice - buyBackPrice)*100/self.sellPrice) - self.slippage)*self.sellQuantity

		profit1_total = (((sellBackPrice - self.buyPrice)*100/self.buyPrice) - self.slippage)*self.buyQuantity
		profit2_total = (((self.sellPrice - buyBackPrice)*100/self.sellPrice) - self.slippage)*self.sellQuantity
		return (profit1 + profit2), (profit1_total + profit2_total)

	def checkDailyMTM(self,buyBackPrice, sellBackPrice):
		profit1 = ((sellBackPrice - self.longMTMprice)*100/self.buyPrice)*self.buyQuantity
		profit2 = ((self.shortMTMprice - buyBackPrice)*100/self.sellPrice)*self.sellQuantity
		self.longMTMprice = sellBackPrice
		self.shortMTMprice = buyBackPrice
		return (profit1 + profit2)

	def checkDailyMTM_30m(self,buyBackPrice, sellBackPrice, cutSlippage = False):
		try:
			profit1 = (((float(sellBackPrice) - self.longMTMprice_30m)*100/self.buyPrice) - (self.slippage if cutSlippage else 0))*self.buyQuantity
			profit2 = (((self.shortMTMprice_30m - float(buyBackPrice))*100/self.sellPrice) - (self.slippage if cutSlippage else 0))*self.sellQuantity
			self.longMTMprice_30m = float(sellBackPrice)
			self.shortMTMprice_30m = float(buyBackPrice)
			return (profit1 + profit2)
		except TypeError:
			return 0