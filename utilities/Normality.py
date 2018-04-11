import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import scipy.stats as stats

def createhistogram(data, filename):
	gs = gridspec.GridSpec(2,1)
	plt.close()
	plt.figure(figsize = (5,8))
	plt.subplot(gs[0,0])
	plt.style.use('ggplot')
	plt.rcParams['axes.facecolor']='white'
	plt.rcParams['grid.color']='gainsboro'
	plt.plot(data, color = 'red', linewidth = 0.8)
	plt.subplot(gs[1,0])
	sns.set_style("whitegrid")
	sns.distplot(data, rug = True)
	plt.tight_layout()
	plt.savefig(filename)

def skewness(data):
	return stats.skew(data)

def kurtosis(data):
	return stats.kurtosis(data)

#Tests
def anderson_darling(data):
	mean = np.mean(data)
	std = np.std(data)
	data = (data - mean)/std
	return stats.anderson(data,"norm")

def shapiro_wilk(data):
	mean = np.mean(data)
	std = np.std(data)
	data = (data - mean)/std
	return stats.shapiro(data)

def jarque_bera(data):
	mean = np.mean(data)
	std = np.std(data)
	data = (data - mean)/std
	return stats.jarque_bera(data)

def kolmogorov_smirnov(data):
	mean = np.mean(data)
	std = np.std(data)
	data = (data - mean)/std
	return stats.kstest(data,"norm")

def skewness_Test(data):
	mean = np.mean(data)
	std = np.std(data)
	data = (data - mean)/std
	return stats.skewtest(data)

def kurtosis_Test(data):
	mean = np.mean(data)
	std = np.std(data)
	data = (data - mean)/std
	return stats.kurtosistest(data)