import sys
sys.path.append('/home/ishan/Desktop/Ishan/Stock Data/Code Files')
sys.path.append('/home/ishan/Desktop/Ishan/Stock Data/Code Files/Strategy')

import pickle
import pandas as pd
import numpy as np
from utilities.UtilityFunctions import UtilityFunctions
from sklearn.cross_validation import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import LinearRegression
from sklearn import metrics
from sklearn import svm

class PredictiveModel:
	def __init__(self, columns, checkPoints = None, saveDir = None):
		exec(UtilityFunctions.initializeFunctionArguments(PredictiveModel.__init__))
		if(checkPoints is not None):
			self.initialize()
		else:
			self.dataFrame = pd.DataFrame(columns = columns)
			self.regressionRowCount = 0

	def initialize(self):
		self.dataFrame = {}
		self.regressionRowCount = {}
		for checkPoint in self.checkPoints:
			self.dataFrame[checkPoint] = pd.DataFrame(columns = self.columns)
			self.regressionRowCount[checkPoint] = 0
		self.addCount = 0

	def saveDataFrames(self):
		for checkPoint in self.checkPoints:
			try:
				df = pd.read_csv(self.saveDir + '/data_' + str(checkPoint) + '.csv')
				df = df[self.columns]
				dfNew = pd.concat([df, self.dataFrame[checkPoint]])
				dfNew.to_csv(self.saveDir + '/data_' + str(checkPoint) + '.csv')
			except FileNotFoundError:
				self.dataFrame[checkPoint].to_csv(self.saveDir + '/data_' + str(checkPoint) + '.csv')

	def add(self,row, checkPoint = None):
		if(checkPoint is not None):
			self.dataFrame[checkPoint].loc[self.regressionRowCount[checkPoint]] = row
			self.dataFrame[checkPoint] = self.dataFrame[checkPoint].dropna(how = 'any')
			self.regressionRowCount[checkPoint] += 1
		else:
			self.dataFrame.loc[self.regressionRowCount] = row
			self.dataFrame = self.dataFrame.dropna(how = 'any')
			self.regressionRowCount += 1

		if(self.saveDir):
			self.addCount += 1
			if(self.addCount == 1000):
				self.saveDataFrames()
				self.initialize()

	def saveRegressionDF(self,filename):
		with open(filename, 'wb') as f:
			pickle.dump(self.dataFrame, f)

	def saveRegressionDFasCSV(self,filename):
		self.regressionDf.to_csv(filename)

	def saveLogModel(self,filename):
		with open(filename, 'wb') as f:
			pickle.dump(self.logModel, f)

	def getPositiveToNegativeRatio(self, targetFeature):
		try:
			return self.dataFrame[targetFeature].value_counts()[1]/self.dataFrame[targetFeature].value_counts()[0]
		except KeyError:
			return 0
		except IndexError:
			return 0
		except ZeroDivisionError:
			return 10000000
	
	def createLogisticModel(self,trainFeatures, targetFeature, splitRatio = 0.5):
		self.train_x, self.test_x, self.train_y, self.test_y = train_test_split(self.dataFrame[trainFeatures], self.dataFrame[targetFeature], train_size=splitRatio)
		logistic_regression_model = LogisticRegression(class_weight = 'balanced')
		logistic_regression_model.fit(self.train_x, self.train_y)
		predictedResults = logistic_regression_model.predict(self.test_x)
		self.logModel = logistic_regression_model
		return logistic_regression_model,logistic_regression_model.score(self.train_x,self.train_y), logistic_regression_model.score(self.test_x,self.test_y), metrics.precision_score(y_pred = predictedResults, y_true = self.test_y), metrics.precision_score(y_pred = abs(predictedResults -1), y_true = abs(self.test_y - 1))

	def createLinearModel(self,trainFeatures, targetFeature, splitRatio = 0.5):
		self.train_x, self.test_x, self.train_y, self.test_y = train_test_split(self.dataFrame[trainFeatures], self.dataFrame[targetFeature], train_size=splitRatio)
		linear_regression_model = LinearRegression()
		linear_regression_model.fit(self.train_x, self.train_y)
		predictedResults = linear_regression_model.predict(self.test_x)
		self.logModel = linear_regression_model
		return linear_regression_model,linear_regression_model.score(self.train_x,self.train_y), linear_regression_model.score(self.test_x,self.test_y), metrics.precision_score(y_pred = predictedResults, y_true = self.test_y), metrics.precision_score(y_pred = abs(predictedResults -1), y_true = abs(self.test_y - 1))

	def createSVMlinearModel(self,trainFeatures, targetFeature,splitRatio = 0.5, param = 1.0):
		self.train_x, self.test_x, self.train_y, self.test_y = train_test_split(self.dataFrame[trainFeatures], self.dataFrame[targetFeature], train_size=splitRatio)
		svmModel = svc = svm.SVC(kernel='linear', C=param).fit(self.train_x, self.train_y)
		predictedResults = svmModel.predict(self.test_x)
		return svmModel,svmModel.score(self.train_x,self.train_y), svmModel.score(self.test_x,self.test_y), metrics.precision_score(y_pred = predictedResults, y_true = self.test_y), metrics.precision_score(y_pred = abs(predictedResults -1), y_true = abs(self.test_y - 1))

	def createSVMrbfModel(self,trainFeatures, targetFeature, splitRatio = 0.5, kernel = 'linear', param = 0.7):
		self.train_x, self.test_x, self.train_y, self.test_y = train_test_split(self.dataFrame[trainFeatures], self.dataFrame[targetFeature], train_size=splitRatio)
		svmModel = svc = svm.SVC(kernel='rbf', gamma=param).fit(self.train_x, self.train_y)
		predictedResults = svmModel.predict(self.test_x)
		return svmModel,svmModel.score(self.train_x,self.train_y), svmModel.score(self.test_x,self.test_y), metrics.precision_score(y_pred = predictedResults, y_true = self.test_y), metrics.precision_score(y_pred = abs(predictedResults -1), y_true = abs(self.test_y - 1))

	def createSVMpolyModel(self,trainFeatures, targetFeature, splitRatio = 0.5, kernel = 'linear', param = 3):
		self.train_x, self.test_x, self.train_y, self.test_y = train_test_split(self.dataFrame[trainFeatures], self.dataFrame[targetFeature], train_size=splitRatio)
		svmModel = svc = svm.SVC(kernel='poly', degree=param).fit(self.train_x, self.train_y)
		predictedResults = svmModel.predict(self.test_x)
		return svmModel,svmModel.score(self.train_x,self.train_y), svmModel.score(self.test_x,self.test_y), metrics.precision_score(y_pred = predictedResults, y_true = self.test_y), metrics.precision_score(y_pred = abs(predictedResults -1), y_true = abs(self.test_y - 1))



