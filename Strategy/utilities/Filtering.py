#In this file, I aim to write down several peeling off techniques.

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import os
import pandas as pd
import scipy.signal as signal

class Filtering:
	def plotData(data, smooth_data, error, filename):
		gs = gridspec.GridSpec(2,1,height_ratios = [1,0.4])
		plt.close()
		plt.subplot(gs[0,0])
		plt.style.use('ggplot')
		plt.rcParams['axes.facecolor']='white'
		plt.rcParams['grid.color']='gainsboro'
		plt.plot(smooth_data, color = 'darkred', linewidth = 0.7)
		plt.plot(data, color = 'salmon',alpha = 0.6)
		plt.subplot(gs[1,0])
		plt.plot(error, color = 'darkred',alpha = 0.6)
		plt.tight_layout()
		plt.savefig(filename)

	def movingAverages(data, window):
		smooth_data = []
		for i in range(window,len(data)):
			smooth_data.append(np.mean(data[i - window: i]))
		peel = np.array(data[-len(smooth_data):]) - np.array(smooth_data)
		return smooth_data, peel

	def detrending(data):
		peel = [0]
		for i in range(1,len(data)):
			peel.append((data[i] - data[i-1])/data[i-1])
		return peel

	def singleExponentialSmoothing(data, alpha):
		smooth_data = [data[0]]
		for dat in data[1:]:
			smooth_data.append(alpha*dat + (1-alpha)*smooth_data[-1])
		peel = np.array(data[-len(smooth_data):]) - np.array(smooth_data)
		return smooth_data, peel


	def fft(data, alpha):
		smooth_data = []
		frequency = np.fft.rfft(data)
		frequency[alpha:] = 0.0
		smooth_data = np.fft.irfft(frequency)
		peel = np.array(data[-len(smooth_data):]) - np.array(smooth_data)
		return smooth_data, peel

	def savitzkyGolay(data, parameters):
		smooth_data = signal.savgol_filter(data, parameters[0], parameters[1])
		peel = np.array(data[-len(smooth_data):]) - np.array(smooth_data)
		return smooth_data, peel