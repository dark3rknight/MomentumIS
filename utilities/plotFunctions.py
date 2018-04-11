import os
import csv
import pandas as pd
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gs

def plotDataWithPeel(data, smooth_data, error, filename):
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

def plotStockData(data, filename):
	plt.close()
	plt.style.use('ggplot')
	plt.rcParams['axes.facecolor']='white'
	plt.rcParams['grid.color']='gainsboro'
	plt.plot(data, color = 'darkred',alpha = 0.8, linewidth = 0.7)
	plt.tight_layout()
	plt.savefig(filename)
