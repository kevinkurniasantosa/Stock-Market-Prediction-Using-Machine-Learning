# For data manipulation
import pandas as pd
import numpy as np
# For read data from local file system
import os 
# For data visualization
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.pylab import rcParams
from matplotlib import style
# For warnings filter
import warnings
from warnings import simplefilter
# Import other libraries
import datetime as dt
from datetime import date, timedelta
import time
import re
import random
# For writing up in excel
import xlsxwriter
import openpyxl
# For model evaluation
from sklearn import metrics
# For checking whether the series is stationary or not
from statsmodels.tsa.stattools import adfuller
# For defining the ACF and PACF
from statsmodels.tsa.stattools import acf, pacf
from scipy.ndimage.interpolation import shift
# For creating and saving the ARIMA model
from statsmodels.tsa.arima_model import ARIMA 
from statsmodels.tsa.arima_model import ARIMAResults
# For plotting the ACF and PACF 
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.graphics.tsaplots import plot_pacf
from statsmodels.tsa.stattools import pacf as pacf_pl
from pandas.plotting import autocorrelation_plot as acf_pl

print('import success')

## FOR IGNORING FUTURE WARNINGS
simplefilter(action='ignore', category=FutureWarning)

### SETUP THE FIGURE SIZE FOR PLOTTING
rcParams['figure.figsize'] = 12,7 # width 8, height 6

### DEFINE TODAY'S DATE
today_date = date.today().strftime('%Y-%m-%d')
print('SCRIPT RUN ON ' + today_date)
print('================================\n')

########################################## CONFIGURATION REQUIRED ##########################################
### Please check/change the parameters below before running

### DATASETS DIRECTORY
time_period_directory = '5_years/'
csv_stock_filename = 'SBRY.L.csv'
# csv_stock_filename = ['TSCO.L.csv', 'SBRY.L.csv']
csv_stock_filepath = '../../datasets/UK Stock Data/' + time_period_directory

### STOCK SPECIFICATIONS
stock_name = 'Sainsbury'
stock_symbol = [s.replace('.L.csv', '') for s in csv_stock_filename]

### HOW MANY NEXT FOLLOWING DAYS DO YOU WANT TO BE PREDICTED
num_of_days_predicted = 7

### SAVE TIME PERIOD IN NEW VARIABLE
x = re.match("(.+)_(.+)/", str(time_period_directory))
time_period = str(x.group(1)) + ' ' + str(x.group(2))

### DEFINE THE FEATURE
feature = 'Close Price'

### PERCENTAGE OF TRAINING AND TESTING DATA
train_percent = 0.8
test_percent = 0.2

### MODEL SPECIFICATIONS
model_filename = 'arima.pkl'
model_name = 'ARIMA'
model_summary_directory = '../.././' 
model_summary_filename = 'Model Summary.xlsx'

########################################################
########################################################

## FOR DIFFERENCING (FOR DEFINING THE INTEGRATED(i) PARAMETER OF THE ARIMA MODEL)
def differencing(dataset, order_cnt):
    diff_values = []
    data = dataset.values
    lag = 1

    for i in range(lag, len(data)):
        value = data[i] - data[i-lag]
        diff_values.append(value)

    order_cnt = order_cnt + 1

    return diff_values, order_cnt

## BECAUSE THE DATA ARE DIFFERENCED AT THE BEGINNING, AFTER THE PREDICTION WAS MADE, THE DATA ARE REQUIRED TO BE DIFFERENCED AGAIN
def inverse_differencing(real_value, pred_value, interval=1):
	return pred_value + real_value

### INITIALLY CHECK IF THE DATA IS A STATIONARY SERIES | return -> stationary or not in boolean variable
def initial_check_stationary(prices):
    # Analysis of the time series data assumes that we are working with a stationary time series.
    # Time series data is almost certainly non-stationary. 
    # So, make it stationary by first differencing the series and using a statistical test to confirm that the result is stationary.
    
    print('---------------------')
    print('Check stationary on the data..')
   
    ## Next, split the time series datainto two contiguous sequences. 
    ## Then calculate the mean and variance of each group of numbers and compare the values.
    series = prices
    series_values = series.values
    split = round(len(series_values) / 2)
    series1, series2 = series_values[0:split], series_values[split:]
    mean1, mean2 = series1.mean(), series2.mean()
    var1, var2 = series1.var(), series2.var()

    ## Preview mean and variance for checking stationary or not
    print('---------------------')
    print('Mean 1 = %f, Mean 2 = %f' % (mean1, mean2))
    print('Variance 1 = %f, Variance 2 = %f' % (var1, var2))

    ## Check the data using statistical significance test of whether the series is stationary. Specifically, using the Augmented Dickey-Fuller test
    critical_values = []
    is_stationaries = False

    adfuller_result = adfuller(series_values)
    print('---------------------')
    print('== Results of Dickey-Fuller Test ==')
    print('ADF Statistic: %f' % adfuller_result[0])
    print('p-value: %f' % adfuller_result[1])
    print('Number of Lags used: %d' % adfuller_result[2])
    print('Number of Observations used: %d' % adfuller_result[3])
    print('Critical Values:')
    for key, value in adfuller_result[4].items():
        critical_values.append(value)
        print('\t%s: %.3f' % (key, value))

    ## If it is stationary, make the boolean to True
    if adfuller_result[0] < critical_values[0]:
        if adfuller_result[0] < critical_values[1]:
            if adfuller_result[0] < critical_values[2]:
                is_stationaries = True

    return is_stationaries

### CHECKING WHETHER THE DATASET IS ALREADY STATIONARY OR NOT | return -> stationary or not stationary in boolean variable
def check_stationary(series_values):
    print('---------------------')
    print('Check stationary on the data..')

    ## Check the data using statistical significance test of whether the series is stationary. Specifically, using the Augmented Dickey-Fuller test
    critical_values = []
    is_stationaries = False

    adfuller_result = adfuller(series_values)
    print('---------------------')
    print('== Results of Dickey-Fuller Test ==')
    print('ADF Statistic: %f' % adfuller_result[0])
    print('p-value: %f' % adfuller_result[1])
    print('Number of Lags used: %d' % adfuller_result[2])
    print('Number of Observations used: %d' % adfuller_result[3])
    print('Critical Values:')
    for key, value in adfuller_result[4].items():
        critical_values.append(value)
        print('\t%s: %.3f' % (key, value))

    ## If it is stationary, make the boolean to True
    if adfuller_result[0] < critical_values[0]:
        if adfuller_result[0] < critical_values[1]:
            if adfuller_result[0] < critical_values[2]:
                is_stationaries = True

    return is_stationaries

### FOR DATA PREPROCESSING | return -> dates data nad prices data
def prepare_data():
    ################################################### DATA PREPROCESSING

    ## Create a dataframe from the CSV data
    df = pd.read_csv(csv_stock_filepath + csv_stock_filename) # Tesco Data

    ## Remove null values
    df = df.dropna()
    df = df.reset_index()
    df = df.drop('index', axis=1)

    ## Sort by Date
    df = df.sort_values('Date')

    ## Set the index to Date
    df.reset_index(inplace=True)
    df['Date'] = pd.to_datetime(df.Date, format='%Y-%m-%d')
    df.set_index("Date", inplace=True)
    df = df.drop('index', axis=1)

    ## Preview the dataframe
    print('---- PREVIEW DATA ----')
    print('NUMBER OF DATA: ' + str(len(df)))
    print('----------------------------')
    print('Head data:\n' + str(df.head()))
    print('----------------------------')
    print('Tail data:\n' + str(df.tail()))
    print('----------------------------')
    print('Data types: \n' + str(df.dtypes))
    print('----------------------------')

    ## Copy df to another dataframe
    dates_df = df.copy()
    dates_df = dates_df.reset_index()

    ## Store the original dates for plotting the predictions
    original_dates = dates_df['Date']

    ## Convert date to integers for training (another method to convert date to num for training)
    dates_df['Date'] = dates_df['Date'].map(mdates.date2num)

    ## Store both dates and prices in new variable
    dates_in_num = dates_df['Date']
    dates = original_dates
    prices = df['Close']

    ## Plotting initial data
    plt.plot(prices)
    plt.title('{} Close Price Preview'.format(stock_name))
    plt.xlabel('Date')
    plt.ylabel('Close Price')
    plt.show()

    ## Plotting the price's count in histogram
    prices.hist(grid=True, rwidth=0.9, color='#607c8e')
    plt.title('Close Price')
    plt.xlabel('Price')
    plt.ylabel('Counts')
    plt.show()

    ## Show the ACF and PACF before the data are differenced
    acf_pacf_plots(prices)

    return dates, prices

## TO GET THE NUMBER OF TIMES THE DATASETS ARE DIFFERENCED TO MAKE IT STATIONARY | return -> the price after differencing and the number of times the data are differenced
def get_differencing_order(prices_data):
    # Call check_stationarity function
    initial_check_stationary(prices_data)
    order_count = 0 # For saving how many times the series data is differenced
    
    while(True):
        prices_diff_values, order_count = differencing(prices_data, order_count)
        print('---------------------')
        print('DIFFERENCING ORDER: {}'.format(order_count)) 
        is_stationary = check_stationary(prices_diff_values)

        if is_stationary == True:
            break
      
    print('---------------------')
    print('No. Differencing Order: {}'.format(order_count))
    plt.plot(prices_diff_values)
    plt.title('Data after Differencing of order {}'.format(order_count))
    plt.xlabel('Dates (in number)')
    plt.ylabel('Close')
    plt.show()

    ## Convert the prices after differecing to Dataframe
    df_prices_diff = pd.DataFrame(prices_diff_values)
    print('---- PREVIEW DATA AFTER DIFFERENCING----')
    print(df_prices_diff)

    return df_prices_diff, order_count

## DETERMINE THE AR AND MA ORDER USING ACF AND PACF PLOTS | return -> the AR and MA ORDER
def acf_pacf_plots(price_after_diff):
    # ARIMA parameters - ARIMA(p,d,q)
    # p: Number of previous values to consider for estimating the current value
    # d: the number of raw observations are differenced (the order count)
    # q: If we consider a moving average to estimate each value, then q indicates the number of previous errors. i.e if q= 3 then we will consider e(t-3), e(t-2) and e(t-1) as inputs of the regressor. Where e(i) = moving_average(i)- actual_value(i)
    
    # Determine p and q using PACF(Partial Auto Correlation Function) and ACF(Auto Correlation Function) graphs respectively

    ## Preview ACF and PACF plot
    print('---------------------')
    print('Preview ACF and PACF plot')
    # plt.subplot(211)
    plot_acf(price_after_diff, ax=plt.gca())
    plt.title('Autocorrelation')
    plt.xlabel('Lag')
    plt.ylabel('AC') 
    plt.show()

    # plt.subplot(212)
    plot_pacf(price_after_diff, ax=plt.gca())
    plt.title('Partial Autocorrelation')
    plt.xlabel('Lag')
    plt.ylabel('Partial AC')    
    plt.show()

    acf_pl(price_after_diff)
    plt.title('Autocorrelation')
    plt.show()

    plot_pacf(price_after_diff)
    plt.title('Partial Autocorrelation')
    plt.xlabel('Lag')
    plt.ylabel('Partial AC')

    ## Specify the axes
    plt.axes([0.5,0.4,0.35,0.35])
    plt.xlabel('Lag')
    plt.ylabel('Partial AC')

    ## Plot the sliced series in red using the current axes
    plt.stem(pacf_pl(price_after_diff)[:5], linefmt='b-', markerfmt='o', basefmt='b')
    plt.show()

## FOR SPLITTING DATASET INTO TRAIN SET AND TEST SET | return -> the train price data, the test price data, the overall date data, the train date data, and the test date data
def split_data(data1, data2, data3):
    ## Split data to train and test
    price_diff_data = data1.values
    price_data = data2.values
    dates_data = data3.values
    price_data = price_data.astype('float32')
    split = int(len(price_data)*train_percent)

    train_diff_data, test_diff_data = price_diff_data[0:split], price_diff_data[split:]
    train_data, test_data = price_data[0:split], price_data[split:]
    train_data_dates, test_data_dates = dates_data[0:split], dates_data[split:]

    ## Convert to numpy date format
    dates_data = np.array(dates_data, dtype='datetime64[D]')
    train_data_dates = np.array(train_data_dates, dtype='datetime64[D]')
    test_data_dates = np.array(test_data_dates, dtype='datetime64[D]')

    return train_diff_data, test_diff_data, train_data, test_data, dates_data, train_data_dates, test_data_dates

## TRAINING AND EVALUATING THE ARIMA MODEL
def train_and_evaluate_arima_model(train_data, test_data, ARIMA_ORDER, is_saved_model):
    predictions = []
    actuals = []
    arima_model_fit = None
    recur_train_data = [x for x in train_data]

    if is_saved_model == False:

        ## Train the model using walk-forward validation technique / rolling forecast 
        for i in range(len(test_data)):
            model = ARIMA(recur_train_data, order=ARIMA_ORDER)
            arima_model_fit = model.fit(disp=0) # Fit the ARIMA model

            output = arima_model_fit.forecast()
            predicted_value = output[0]
            actual_value = test_data[i]

            recur_train_data.append(actual_value)
            predictions.append(predicted_value)
            actuals.append(actual_value)
        
            # print('Predicted Value: %f, Actual Value: %f' % (predicted_value, actual_value))

    elif is_saved_model == True:

        ## Load the saved ARIMA model
        arima_loaded_model = ARIMAResults.load(model_filename)
        arima_model_fit = arima_loaded_model
        # print('Training the ARIMA{} model..'.format(arima_order))

        for i in range(len(test_data)):
            model = ARIMA(recur_train_data, order=ARIMA_ORDER)
            arima_model_fit = model.fit(disp=0) # Fit the ARIMA model

            output = arima_model_fit.forecast()
            predicted_value = output[0]
            actual_value = test_data[i]
    
            recur_train_data.append(actual_value)
            predictions.append(predicted_value)
            actuals.append(actual_value)

    ## Evaluate the ARIMA model using several metrics (Mean Absolute Error, Mean Absolute Percentage Error, Root Mean Squared Error)    
    mae = metrics.mean_absolute_error(actuals, predictions)
    mape = np.mean(np.abs((np.array(actuals) - np.array(predictions)) / np.array(actuals))) * 100
    mse = metrics.mean_squared_error(actuals, predictions)
    rmse = np.sqrt(mse)

    return mae, mape, rmse, predictions, actuals, arima_model_fit

## VISUALIZE THE PREDICTED VALUE BY THE ARIMA MODEL
def visualize_arima_prediction(stock_name, train_data, test_data, dates, train_dates, test_dates, predicted_values):
    print('== VISUALIZE ACTUAL RESULTS vs. PREDICTED RESULTS ==')

    ## Plotting the actual result and the predicted result from ARIMA
    plt.plot(test_dates, test_data, color='blue', label='Real values')
    plt.plot(test_dates, predicted_values, color='orange', label='Predicted values')
    # plt.scatter(test_dates, predicted_values, color='red', label='Predicted values')
    plt.title('ARIMA | {} Stock - Prediction vs. Real Stock Values'.format(stock_name))
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.show()

    ## Plotting the overall data
    plt.plot(train_dates, train_data, color='blue', label='Training Data')
    plt.plot(test_dates, predicted_values, color='green', marker='o', linestyle='dashed', label='Predicted Price')
    plt.plot(test_dates, test_data, color='red', label='Actual Price')
    plt.title('ARIMA | {} Stock Prices Prediction'.format(stock_name))
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()   
    plt.show()

## FOR SAVING THE ARIMA MODEL
def save_arima_model(ARIMA_MODEL):
    ## Save the model
    ARIMA_MODEL.save(model_filename)

######## METHOD 1: HYPERPARAMETER TUNING BY MANUALLY INITIALIZE THE ARIMA(p,d,q)
## FOR DEVELOPING AND EVALUATING THE ARIMA MODEL USING TRAIN AND TEST DATA
def build_arima(d, prices_diff, prices, dates, use_saved_model):
    warnings.filterwarnings("ignore")

    ## IMPORTANT!!!
    ## Define the ARIMA parameters
    arima_AR = 1
    # arima_I = d+1 
    arima_I = 2
    arima_MA = 3

    arima_order = (arima_AR, arima_I, arima_MA)
    arima_param = 'ARIMA' + str(arima_order)
    
    ## Get the train and test data
    train_diff_data, test_diff_data, train_data, test_data, dates_data, train_data_dates, test_data_dates = split_data(prices_diff, prices, dates)

    ## Preview train and test data
    print('== PREVIEW TRAIN AND TEST DATA ==')
    print('TRAIN DATA\n' + str([train_data[x] for x in range(0,5)]))
    print('TEST DATA\n' + str([test_data[x] for x in range(0,5)]))
    print('NUMBER OF TRAIN DATA: ' + str(len(train_data)))
    print('NUMBER OF TEST DATA: ' + str(len(test_data)))

    ################################################### MODEL DEVELOPMENT & EVALUATION
    
    print('------------------------------')
    if use_saved_model == False:
        print('Training the ARIMA{} model..'.format(arima_order))
    elif use_saved_model == True:
        print('Load the ARIMA model..')

    ########################## Technique 1
    ### Method 1: Train the model using normal data
    
    mae, mape, rmse, prediction_values, actual_values, arima_model = train_and_evaluate_arima_model(train_data, test_data, arima_order, use_saved_model)        

    print('-- ARIMA Model Summary --')
    print(arima_model.summary())

    for i in range(len(test_data)):
        print('Predicted Value: %f, Actual Value: %f' % (prediction_values[i], actual_values[i]))

    # for i in range(len(test_data)):
    #     print('Predicted Value: %f, Actual Value: %f' % (prediction_values[i+1], actual_values[i]))

    print('== ARIMA MODEL - PERFORMANCE REPORT ==')
    print('MAE: %.3f' % (mae))
    print('MAPE: %.3f' % (mape))
    print('RMSE: %.3f' % (rmse))
    print('===========================================')

    ########################## Technique 2
    ### Method 2: Train the model using data that has been differenced
        
    # mae, mape, rmse, prediction_values, actual_values, arima_model = train_and_evaluate_arima_model(train_diff_data, test_diff_data, arima_order, use_saved_model)        

    # print('-- ARIMA Model Summary --')
    # print(arima_model.summary())

    # for i in range(len(test_data)-1):
    #     forecast = inverse_differencing(test_data[i-1], prediction_values[i])
    #     print('Predicted Value: %f, Actual Value: %f' % (forecast, test_data[i]))

    # print('== ARIMA MODEL - REPORT PERFORMANCE ==')
    # print('MAE: ' + str(mae))
    # print('MAPE: ' + str(mape))
    # print('RMSE: ' + str(rmse))
    # print('===========================================')

    ################################################### VISUALIZE THE RESULTS

    visualize_arima_prediction(stock_name, train_data, test_data, dates_data, train_data_dates, test_data_dates, prediction_values)

    # ## Save the ARIMA model
    # save_arima_model(arima_model)
    # print('Model saved')

    ## Save model's summary for comparison
    save_model_summary(stock_name, time_period, feature, arima_param, mae, mape, rmse)

######## METHOD 2: HYPERPARAMETER TUNING BY USING GRID SEARCH TO FIND THE MOST OPTIMAL ARIMA(p,d,q)
## FOR DEVELOPING AND EVALUATING THE ARIMA MODEL USING TRAIN AND TEST DATA
def build_arima_grid_search(prices_diff, prices, dates):
    warnings.filterwarnings("ignore")

    ## Get the train and test data
    train_diff_data, test_diff_data, train_data, test_data, dates_data, train_data_dates, test_data_dates = split_data(prices_diff, prices, dates)

    ## Define the possible range of each ARIMA parameters
    p_param = range(0, 6)
    d_param = range(0, 3)
    q_param = range(0, 6)

    ################################################### MODEL EVALUATION

    ## Initialize the score variables as infinite value to find the least score
    best_mae = [float('inf'), float('inf'), float('inf')]
    best_mape = [float('inf'), float('inf'), float('inf')]
    best_rmse = [float('inf'), float('inf'), float('inf')]
    best_arima_model_prediction = None
    prediction_by_best_arima_model = None
    best_arima_order = [None, None, None]

    print('------------------------------')
    print('Searching for the best ARIMA model..')

    ## Evaluate the combinations of p, d, and q values for the ARIMA model
    for p_value in p_param:
        for d_value in d_param:
            for q_value in q_param:
                arima_order = (p_value, d_value, q_value)

                ## Use try and except here because sometimes some ARIMA model parameters are not compatible due to 
                try: 
                    mae, mape, rmse, predictions, actuals, arima_model = train_and_evaluate_arima_model(train_data, test_data, arima_order, False)
                    print('ARIMA%s | RMSE: %.3f' % (arima_order, rmse))

                    ## Find the best 3 RMSE score
                    if rmse < best_rmse[0]:
                        # RMSE
                        best_rmse[2] = best_rmse[1]
                        best_rmse[1] = best_rmse[0]
                        best_rmse[0] = rmse  
                        # MAE
                        best_mae[2] = best_mae[1]
                        best_mae[1] = best_mae[0]
                        best_mae[0] = mae  
                        # MAPE
                        best_mape[2] = best_mape[1]
                        best_mape[1] = best_mape[0]
                        best_mape[0] = mape 
                        best_arima_order[0] = arima_order
                        prediction_by_best_arima_model = predictions
                    elif rmse < best_rmse[1]:
                        # RMSE
                        best_rmse[2] = best_rmse[1]
                        best_rmse[1] = rmse
                        # MAE
                        best_mae[2] = best_mae[1]
                        best_mae[1] = mae
                        # MAPE
                        best_mape[2] = best_mape[1]
                        best_mape[1] = mape
                        best_arima_order[1] = arima_order
                    elif rmse < best_rmse[2]:
                        # RMSE
                        best_rmse[2] = rmse
                        # MAE
                        best_mae[2] = mae
                        # MAPE
                        best_mape[2] = mape
                        best_arima_order[2] = arima_order

                except Exception as err:
                    # print('Error: ' + str(err))
                    continue 
                  
    print('===============================')
    print('Top 3 best performing ARIMA models:')
    for k in range(3):
        print('ARIMA%s | RMSE: %.3f, MAE: %.3f, MAPE: %.3f' % (best_arima_order[k], best_rmse[k], best_mae[k], best_mape[k]))
    
    visualize_arima_prediction(stock_name, train_data, test_data, dates_data, train_data_dates, test_data_dates, prediction_by_best_arima_model)
    print('BEST ARIMA MODEL: ARIMA{}'.format(best_arima_order[0]))
    
## FOR FORECASTING OUT-OF-SAMPLE DATA 
def arima_forecast_future_prices(p, d, q, prices_diff, prices, dates):
    num_days = num_of_days_predicted

    ## Get the train and test data
    train_diff_data, test_diff_data, train_data, test_data, dates_data, train_data_dates, test_data_dates = split_data(prices_diff, prices, dates)

    ###### FORECASTING FUTURE PRICES
    ### One-Step Out-of-Sample Forecast
    print('===========================')
    print('- One-Step Out-of-Sample Forecast -')
    model_test1 = ARIMA(train_data, order=(p,d,q)) # 1,1,2
    model_fit1 = model_test1.fit(disp=0)
    forecasts1 = model_fit1.forecast()[0]
    print('Day 1: ' + str(forecasts1[0]))

    ### Multi-step out-of-sample forecast
    print('----------------------------')
    print('- Multi-Step Out-of-Sample Forecast -')
    model_test2 = ARIMA(train_data, order=(p,d,q))
    model_fit2 = model_test2.fit(disp=0)
    forecasts2 = model_fit2.forecast(steps=num_days)[0]
    for x, future_price in enumerate(forecasts2):
        print('Day ' + str(x+1) + ': ' + str(future_price))
    print('===========================')

## SAVING THE MODEL SUMMARY FOR MODEL COMPARISON
def save_model_summary(stock_name, time_period, feature, hyperparameter, mae, mape, rmse):
    model_summary = {
        'A': stock_name, # Dataset
        'B': time_period, # Period
        'C': feature, # Features
        'D': hyperparameter, # Hyperparameters
        'E': '%.3f' % (mae), # MAE
        'F': '%.3f' % (mape), # MAPE
        'G': '%.3f' % (rmse) # RMSE
    }

    ## Load workbook
    wb = openpyxl.load_workbook(model_summary_directory + model_summary_filename)
    
    ## Choose the sheet based on the model name
    sheet = wb.get_sheet_by_name(model_name)
    
    ## Start to write in a new line
    row_num = sheet.max_row + 1

    ## Write the model summary on specific row
    for key, value in model_summary.items():     
        sheet[str(key) + str(row_num)].value = str(value)

    wb.save(filename=model_summary_directory+model_summary_filename) 
    print('Model summary successfully saved')

## MAIN FUNCTION
def main():
    while True:
        try:
            train_or_load_model = int(input('Do you want to load the saved model?\n1. YES\n2. NO\nChoose (1/2): '))
            if train_or_load_model != 1 and train_or_load_model != 2:
                print('Wrong input, try again..')
                print('-------------------------')
            else:
                if train_or_load_model == 1:
                    use_saved_model = True
                elif train_or_load_model == 2:
                    use_saved_model = False
                break
        except Exception as err:
            print('Wrong input: ' + str(err))
            continue

    DATES, PRICES = prepare_data()

    ### MODEL DEVELOPMENT
    PRICES_AFTER_DIFF, INTEGRATED_PARAM = get_differencing_order(PRICES) # Get the differenced data and the ARIMA(d)
    acf_pacf_plots(PRICES_AFTER_DIFF) # Observe the ACF and PACF plots

    build_arima(INTEGRATED_PARAM, PRICES_AFTER_DIFF, PRICES, DATES, use_saved_model)
    # build_arima_grid_search(PRICES_AFTER_DIFF, PRICES, DATES)
    
    ## Uncomment below if want to forecast out-of-sample prices
    # arima_forecast_future_prices(P_PACF, INTEGRATED_PARAM, Q_ACF, PRICES_AFTER_DIFF, PRICES, DATES)

if __name__ == '__main__':
    main()
