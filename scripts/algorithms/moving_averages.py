import pandas as pd
import numpy as np
from pandas_datareader import data
import os # For read data from local file system
import random # For initialize the tensorflow
import sys 
import datetime
# For plotting
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.pylab import rcParams
from matplotlib import style
# For plotting OHLC candlesticks
import plotly.graph_objects as go
# For warnings filter
from warnings import simplefilter
import datetime
from datetime import date, timedelta
import re

print('import success')

### SETUP THE FIGURE SIZE FOR PLOT
rcParams['figure.figsize'] = 12,6

### TO IGNORE FUTURE WARNINGS
simplefilter(action='ignore', category=FutureWarning)

### DEFINE TODAY'S DATE 
today_date = date.today().strftime('%Y-%m-%d')
print('SCRIPT RUN ON ' + today_date)
print('================================')

########################################## CONFIGURATION REQUIRED ##########################################
### Please check/change the parameters below before running

stock_name = ['Tesco', 'Sainsbury']
# stock_name = 'Tesco'
csv_stock_symbol = ['TSCO.L.csv', 'SBRY.L.csv']
time_period_directory = '5_years/'

### MOVING AVERAGES PERIODS
mavg_period1 = 10
mavg_period2 = 50
mavg_period3 = 100

########################################################
########################################################

def moving_average():

    for i in range(3):
        csv_filepath = '../../datasets/UK Stock Data/' + time_period_directory + csv_stock_symbol[i]

        ## Read csv file
        df = pd.read_csv(csv_filepath)

        ## Remove null values
        df = df.dropna()
        df = df.reset_index()
        df = df.drop('index', axis=1)

        ## Sort by Date
        df = df.sort_values('Date')

        # ## Plotting structures: Date, Open, High, Low, Close
        # fig = go.Figure(data=[go.Candlesti``ck(x=df['Date'],
        # open=df['Open'],
        # high=df['High'],
        # low=df['Low'],
        # close=df['Close'])])

        # fig.show()

        ## Reset index
        df.reset_index(inplace=True)
        df['Date'] = pd.to_datetime(df.Date, format='%Y-%m-%d')
        df.set_index("Date", inplace=True)
        df = df.drop('index', axis=1)

        ## Check the result
        print('---- PREVIEW DATA ----')
        print('NUMBER OF DATA: ' + str(len(df)))
        print('----------------------------')
        print('Head data:\n' + str(df.head()))
        print('----------------------------')
        print('Tail data:\n' + str(df.tail()))
        print('----------------------------')

        ## Store prices to price variable
        prices = df['Adj Close']

        ## Plotting initial data
        print('Plotting initial data..')
        plt.plot(prices)
        plt.title('{} Close Price Preview'.format(stock_name[i]))
        plt.xlabel('Date')
        plt.ylabel('Adjusted Close Price')
        plt.show()

        ############################### SIMPLE MOVING AVERAGES

        ## Formula SMA: price(1) + price(2) + ... + price(n) / n, where: n is the time periods 

        mavg1 = prices.rolling(window=mavg_period1).mean()
        mavg2 = prices.rolling(window=mavg_period2).mean()
        mavg3 = prices.rolling(window=mavg_period3).mean()

        print('Plotting Simple Moving Average..')
        plt.plot(prices, label='Close Price')
        plt.plot(mavg1, label='SMA ({} days)'.format(mavg_period1))
        plt.plot(mavg2, label='SMA ({} days)'.format(mavg_period2))
        plt.plot(mavg3, label='SMA ({} days)'.format(mavg_period3))
        plt.title('{} Stock Price - Simple Moving Averages Overview'.format(stock_name[i]))
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.show()

        ############################### EXPONENTIAL MOVING AVERAGES

        ## Formula EMA: (price(n) x P) + (EMA(n-1) x (1-P)), where: n is the time periods and P = 2/(N+1)

        emavg1 = prices.ewm(span=mavg_period1, adjust=False).mean() # adjust = true -> divide by decaying adjustment factor in beginning periods to account for imbalance in relative weightings (viewing EWMA as a moving average)
        emavg2 = prices.ewm(span=mavg_period2, adjust=False).mean()
        emavg3 = prices.ewm(span=mavg_period3, adjust=False).mean()

        print('Plotting Exponential Moving Average..')
        plt.plot(prices, label='Close Price')
        plt.plot(emavg1, label='EMA ({} days)'.format(mavg_period1))
        plt.plot(emavg2, label='EMA ({} days)'.format(mavg_period2))
        plt.plot(emavg3, label='EMA ({} days)'.format(mavg_period3))
        plt.title('{} Stock Price - Exponential Moving Averages Overview'.format(stock_name[i]))
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.show()

if __name__ == '__main__':
    moving_average()



