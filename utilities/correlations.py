import pandas as pd
import scipy.stats as stats

def findPos(num,lis):
	for i in range(len(lis)-1):
		if(num >= lis[i]):
			if(num < lis[i+1]):
				return i
	return(len(lis) - 1)

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

def findandfixPatch(point1,point2,patchList, fix = False):
	inFlag = False
	start = findPos(point1,patchList)
	end = findPos(point2, patchList)
	last = patchList[-1]
	if(start%2 == 0):
		startInFlag = False
	else:
		startInFlag = True

	if(end%2 == 0):
		endInFlag = False
	else:
		endInFlag = True

	if(start == end):
		if(startInFlag == True):
			return 'Immersed',patchList
		else:
			if(fix):
				if((point1 - patchList[start])>1):
					if((patchList[start + 1] - point2) > 1):
						patchList = patchList[:start+1] + [point1,point2] + patchList[start+1:]
					else:
						patchList[start + 1] = point1
				else:
					if((patchList[start + 1] - point2) > 1):
						patchList[start] = point2
					else:
						patchList = patchList[:start] + patchList[
						start+2:]
			if(patchList[0] != 0):
				patchList = [0,0] + patchList
			if(patchList[-1] != last):
				patchList.append(last)
					
			return 'Outside',patchList
	else:
		if(fix):
			if(startInFlag == True)and(endInFlag == True):
				patchList = patchList[:start+1] + patchList[end+1:]
			elif(startInFlag == False)and(endInFlag == False):
				patchList = patchList[:start+1] + [point1,point2] + patchList[end+1:]
			elif(startInFlag == False)and(endInFlag == True):
				patchList = patchList[:start+1] + [point1] + patchList[end + 1:]
			else:
				patchList = patchList[:start+1] + [point2] + patchList[end + 1:]

			if(patchList[0] != 0):
				patchList = [0,0] + patchList
			if(patchList[-1] != last):
				patchList.append(last)
		return 'Overlapped',patchList

def calculateCorrelations(df, stockName1, stockName2, maxLag, correlationWindows, threshold,jump,lagJump):
	stock1 = list(df[stockName1])
	stock2 = list(df[stockName2])

	correlationWindows.sort()
	correlationWindows.reverse()

	correlations = {}

	patchList1 = [0,len(stock1)]
	patchList2 = [0,len(stock2)]

	correlationMap1 = {}
	correlationMap2 = {}

	for windowSize in correlationWindows:
		print(windowSize)
		correlations[windowSize] = []

		for i in range(0,len(stock1) - windowSize,jump):
			start1 = i
			end1 = i + windowSize
			ans,lis = findandfixPatch(start1,end1,patchList1,fix = False)
			if(ans == 'Immersed'):
				continue
			maxPosCorr = 0
			PosCorrXY = []
			PosLag = 0
			foundFlag = False
			maxNegCorr = 0
			NegCorrXY = []
			NegLag = 0
			for lag in range(-maxLag,maxLag + 1,lagJump):
				start2 = start1 + lag
				end2 = end1 + lag

				if(start2 < 0):
					continue

				if(end2 >= len(stock2)):
					continue

				corr = stats.pearsonr(stock1[start1:end1], stock2[start2:end2])[0]

				if(abs(corr) > threshold):
					foundFlag = True
					if(corr > 0):
						if(corr > maxPosCorr):
							maxPosCorr = corr
							PosCorrXY = [start2,end2]
							PosLag = lag
					else:
						if(corr < maxNegCorr):
							maxNegCorr = corr
							NegCorrXY = [start2,end2]
							NegLag = lag

			if(foundFlag):
				if(abs(maxPosCorr - maxNegCorr) < 0.15):
					if(abs(PosLag) < abs(NegLag)):
						finalCorrelation = maxPosCorr
						finalXY = PosCorrXY
						finalLag = PosLag
					else:
						finalCorrelation = maxNegCorr
						finalXY = NegCorrXY
						finalLag = NegLag

				else:
					if(abs(maxPosCorr) > abs(maxNegCorr)):
						finalCorrelation = maxPosCorr
						finalXY = PosCorrXY
						finalLag = PosLag
					else:
						finalCorrelation = maxNegCorr
						finalXY = NegCorrXY
						finalLag = NegLag
				correlations[windowSize].append([finalCorrelation,[start1,end1],finalXY,finalLag])
				correlationMap1[(start1 +  end1)/2] = finalCorrelation
				correlationMap2[(finalXY[0] +  finalXY[1])/2] = finalCorrelation
				findandfixPatch(start1,end1,patchList1,fix = True)
				findandfixPatch(finalXY[0],finalXY[1],patchList2,fix = True)
	return correlations,patchList1,patchList2,correlationMap1,correlationMap2