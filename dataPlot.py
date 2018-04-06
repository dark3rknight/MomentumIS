'''
Author: Sarthak Bajaj
Compamny Rights: Crimson Financials Pvt. Ltd
'''

import matplotlib.pyplot as plt


def multi_subPlot( vals1, label1, vals2, label2, vals3 = None, label3 = None, vals4 = None, label4 = None):
    fig = plt.figure()

    ax1 = fig.add_subplot(312)
    ax1.plot(vals1, color = 'darkred', linewidth = 0.6, label = label1)
    ax2 = fig.add_subplot(311)
    ax2.plot(vals2, color = 'green', linewidth = 0.6, label = label2)
    if vals3 != None:
        ax2.plot(vals3, color = 'blue', linewidth = 0.6, label = label3)
    if vals4 != None:
        ax3 = fig.add_subplot(313)
        ax3.plot(vals4,color = 'salmon',linewidth = 0.6, label = label4)
        ax3.grid(True)
        ax3.legend()     
    ax1.grid(True)
    ax2.grid(True)
    ax1.legend()
    ax2.legend()
    plt.show()

def multiAxis_LabeledPlot(vals1, label1, vals2 = None, label2 = None, vals3 = None, label3 = None, vals4 = None, label4 = None):
    plt.close()
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.plot(vals1, color = 'darkred', linewidth = 0.6, label = label1)
    if vals2 != None:
        ax1.plot(vals2, color = 'blue', linewidth = 0.6, label = label2)
    if vals3 != None:
       ax1.plot(vals3, color = 'green', linewidth = 0.6, label = label3)
    if vals4 != None:
        ax4 = ax1.twinx()
        ax4.plot(vals4, color = 'salmon', linewidth = 0.6, label = label4)
    ax1.grid(True)
    ax1.legend()
    plt.legend()
    plt.show()


def multiplePlots(vals1, label1, vals2 = None, label2 = None, vals3 = None, label3 = None, vals4 = None, label4 = None):
    plt.close()
    plt.plot(vals1, color = 'darkred', linewidth = 0.6, label = label1)
    if vals2 != None:
        plt.plot(vals2, color = 'salmon', linewidth = 0.6, label = label2)
    if vals3 != None:
        plt.plot(vals3, color = 'green', linewidth = 0.6, label = label3)
    if vals4 != None:
        plt.plot(vals4, color = 'blue', linewidth = 0.6, label = label4)
    plt.grid(True)
    plt.legend()
    plt.show()
