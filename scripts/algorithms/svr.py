# For data manipulation
import csv
import numpy as np 
import pandas as pd
# For creating SVR model
from sklearn.svm import SVR
# For creating SVM model
from sklearn import svm, preprocessing
from sklearn.model_selection import cross_validate
from sklearn import metrics # For evaluation
from sklearn.model_selection import train_test_split
# For plotting data
import matplotlib.pyplot as plt 
from matplotlib.pylab import rcParams
# Import warnings filter
from warnings import simplefilter
# For writing up in excel
import xlsxwriter
import openpyxl
# For saving the model
import pickle
# etc
import datetime
from datetime import date, timedelta
import os, os.path
import re
import time

print('import success')

## FOR IGNORING FUTURE WARNINGS
simplefilter(action='ignore', category=FutureWarning)

### SETUP THE FIGURE SIZE FOR PLOTTING
rcParams['figure.figsize'] = 10,6 # width 8, height 6

### DEFINE TODAY'S DATE
today_date = date.today().strftime('%Y-%m-%d')
print('SCRIPT RUN ON ' + today_date)
print('================================\n')

########################################## CONFIGURATION REQUIRED ##########################################

### PERCENTAGE OF TRAINING AND TESTING DATA
train_percent = 0.8
test_percent = 0.2

### CSV FILEPATH
time_period_directory = '1_year/'
stock_name = 'Tesco'
csv_stock_name = 'TSCO.L.csv'
csv_stock_path = '../../datasets/UK Stock Data/' + time_period_directory

### SAVE TIME PERIOD IN NEW VARIABLE
x = re.match("(.+)_(.+)/", str(time_period_directory))
time_period = str(x.group(1)) + ' ' + str(x.group(2))

### DEFINE THE FEATURE
feature = 'Date'

### MODEL SPECIFICATIONS
model_name = 'SVR'
model_summary_directory = '../.././' 
model_summary_filename = 'Model Summary.xlsx'

########################################################
########################################################

### PREPROCESS DATA FIRST | return -> dates, prices and the original dates
def preprocess_data():
    ################################################### DATA PREPROCESSING

    ## Read data
    df = pd.read_csv(csv_stock_path + csv_stock_name) # Tesco Data

    ## Remove null values
    df = df.dropna()
    df = df.reset_index()
    df = df.drop('index', axis=1)

    ## Sort by Date
    df = df.sort_values('Date')

    ## Set the index to Date
    df.reset_index(inplace=True)

    ## Get date values
    dates = [] 
    # for i in range(len(df)):
    #     dates.append(int(df['Date'][i].split('-')[2]))

    df['Date'] = pd.to_datetime(df.Date, format='%Y-%m-%d')
    original_dates = df['Date'] # Save the original dates for plotting
    df.set_index("Date", inplace=True)
    df = df.drop('index', axis=1)

    ## Put dataframe to new variable called 'data'
    data = df.copy()

    ## Preview the data
    print('---- PREVIEW INITIAL DATA ----')
    print('Head data:\n' + str(data.head()))
    print('Tail data:\n' + str(data.tail()))

    ## Initialize the data X and Y variable (x: date, y: close price)
    prices = data['Close']
    for i in range(len(data)):
        dates.append(i)

    print(dates)
        
    ## Plotting initial data
    plt.plot(prices)
    plt.title('{} Close Price Preview'.format(stock_name))
    plt.xlabel('Date')
    plt.ylabel('Close Price')
    plt.show()
    
    return dates, prices, original_dates

def split_data(data_1, data_2, data_3):

    ## Convert to a list
    dates_data = data_1 # Already in a list
    price_data = data_2.tolist()
    original_dates_data = data_3.tolist()

    ## Split the data into train data and test data
    split = int(len(price_data)*train_percent)
    x_train_data, x_test_data = dates_data[0:split], dates_data[split:]
    y_train_data, y_test_data = price_data[0:split], price_data[split:]
    dates_train_data, dates_test_data = original_dates_data[0:split], original_dates_data[split:]

    ## Convert to numpy date format
    dates_train_data = np.array(dates_train_data, dtype='datetime64[D]')
    dates_test_data = np.array(dates_test_data, dtype='datetime64[D]')

    return x_train_data, x_test_data, y_train_data, y_test_data, dates_train_data, dates_test_data

### FOR MAKING PREDICTION | return -> predicted price on specific date on linear, polynomial and RBF model
def svr_predict(dates, prices, original_dates):

    x_train, x_test, y_train, y_test, dates_train, dates_test = split_data(dates, prices, original_dates)

    # Preview the first five X Train, Y Train, X Test, Y Test data
    print('== PREVIEW TRAIN AND TEST DATA')
    print('---------------------------------')
    print('X TRAIN:\n' + str([x_train[x] for x in range(0,5)]))
    print('Y TRAIN:\n' + str([y_train[x] for x in range(0,5)]))
    print('---------------------------------')
    print('X TEST:\n' + str([x_test[x] for x in range(0,5)]))
    print('Y TEST:\n' + str([y_test[x] for x in range(0,5)]))

    ## Convert to 1xn dimension
    x_train = np.reshape(x_train, (len(x_train), 1))
    x_test = np.reshape(x_test, (len(x_test), 1))

    # x : Training vector {array-like, sparse matrix}, shape (n_samples, n_features)
    # y : Target vector relative to x array-like, shape (n_samples,)

    ################################################### MODEL DEVELOPMENT

    svm_linear_param = {
        'kernel': 'linear',
        'C': 1e3
    }

    svm_polynomial_param = {
        'kernel': 'poly',
        'C': 1e3,
        'degree': 2
    }

    svm_rbf_param = {
        'kernel': 'rbf',
        'C': 1e3,
        'gamma': 0.1
    }

    ## Define hyperparameters for the SVR model
    svr_linear = SVR(kernel=svm_linear_param['kernel'], C=svm_linear_param['C']) # For linear classification, Epsilon = 0.1
    svr_polynomial = SVR(kernel=svm_polynomial_param['kernel'], C=svm_polynomial_param['C'], degree=svm_polynomial_param['degree']) # Polynomial order = 2, Epsilon = 0.1
    svr_rbf = SVR(kernel=svm_rbf_param['kernel'], C=svm_rbf_param['C'], gamma=svm_rbf_param['gamma']) # For non-linear classification, Epsilon = 0.1, Gamma = 0.1, Degree = 3

    ## Fit training data (x = dates, y = prices)
    print('----------------------------')
    print('Training SVR linear model..')
    svr_linear.fit(x_train, y_train)
    print('Training SVR polynomial model..')
    svr_polynomial.fit(x_train, y_train)
    print('Training SVR RBF model..')
    svr_rbf.fit(x_train, y_train)

    y_pred_linear = svr_linear.predict(x_test)
    y_pred_polynomial = svr_polynomial.predict(x_test)
    y_pred_rbf = svr_rbf.predict(x_test)

    pkl_filename1 = 'svr linear'
    pkl_filename2 = 'svr polynomial'
    pkl_filename3 = 'svr rbf'
    with open(pkl_filename1, 'wb') as file:
        pickle.dump(svr_linear, file)
    with open(pkl_filename2, 'wb') as file:
        pickle.dump(svr_polynomial, file)
    with open(pkl_filename3, 'wb') as file:
        pickle.dump(svr_rbf, file)

    ################################################### MODEL EVALUATION

    ## Evaluate the model using several metrics (Mean Absolute Error, Mean Squared Error, Root Mean Squared Error)
    mae_linear = metrics.mean_absolute_error(y_test, y_pred_linear)
    mae_polynomial = metrics.mean_absolute_error(y_test, y_pred_polynomial)
    mae_rbf = metrics.mean_absolute_error(y_test, y_pred_rbf)
    rmse_linear = np.sqrt(np.mean(np.power((np.array(y_test)-np.array(y_pred_linear)), 2)))
    rmse_polynomial = np.sqrt(np.mean(np.power((np.array(y_test)-np.array(y_pred_polynomial)), 2)))
    rmse_rbf = np.sqrt(np.mean(np.power((np.array(y_test)-np.array(y_pred_rbf)), 2)))
    
    print('-------------------------------------------')
    print('=== SVR Linear ===')
    print('MAE: ' + str(mae_linear))
    print('RMSE: ' + str(rmse_linear))
    print('=== SVR Polynomial ===')
    print('MAE: ' + str(mae_polynomial))
    print('RMSE: ' + str(rmse_polynomial))
    print('=== SVR Radial Basis Function ===')
    print('MAE: ' + str(mae_rbf))
    print('RMSE: ' + str(rmse_rbf))
    print('===========================================')

    ################################################### MODEL VISUALIZATION

    ## Compare the results between models for further observation 
    result_linear = pd.DataFrame({'Actual': y_test, 'Predicted': y_pred_linear})
    result_polynomial = pd.DataFrame({'Actual': y_test, 'Predicted': y_pred_polynomial})
    result_rbf = pd.DataFrame({'Actual': y_test, 'Predicted': y_pred_rbf})
    print('== RESULTS COMPARISON ON TESTING DATA ==')
    print(result_linear)
    print('--------------------------')
    print(result_polynomial)
    print('--------------------------')
    print(result_rbf)

    ## Plotting results made by SVR
    print('== VISUALIZE RESULTS ==')
    plt.scatter(dates_test, y_test, color='orange', label='Actual Values')
    plt.plot(dates_test, y_pred_linear, color='green', label='Linear model')
    plt.plot(dates_test, y_pred_polynomial, color='blue', label='Polynomial model')
    plt.plot(dates_test, y_pred_rbf, color='red', label='RBF model')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.title('Support Vector Regression | Predicted Values vs. Real Values')
    plt.legend()
    plt.show()

    ## Plotting the overall data
    plt.plot(dates_train, y_train, color='steelblue', label='Training Data')
    plt.plot(dates_test, y_test, color='cyan', label='Test Data')
    plt.plot(dates_test, y_pred_linear, c='green', label='SVR Linear result')
    plt.plot(dates_test, y_pred_polynomial, c='blue', label='SVR Polynomial result')
    plt.plot(dates_test, y_pred_rbf, c='red', label='SVR RBF result')
    plt.title('Support Vector Regression | {} Stock Prices Prediction'.format(stock_name))
    plt.xlabel('Dates')
    plt.ylabel('Prices')
    plt.legend()   
    plt.show()

    save_model_summary(stock_name, time_period, feature, svm_linear_param, mae_linear, rmse_linear)
    save_model_summary(stock_name, time_period, feature, svm_polynomial_param, mae_polynomial, rmse_polynomial)
    save_model_summary(stock_name, time_period, feature, svm_rbf_param, mae_rbf, rmse_rbf)

## SAVING THE MODEL SUMMARY FOR MODEL COMPARISON
def save_model_summary(stock_name, time_period, feature, hyperparameter, mae, rmse):
    model_summary = {
        'A': stock_name, # Dataset
        'B': time_period, # Period
        'C': feature, # Features
        'D': hyperparameter, # Hyperparameters
        'E': '%.3f' % (mae), # MAE
        'F': '%.3f' % (rmse) # RMSE
    }

    ## Load workbook
    wb = openpyxl.load_workbook(model_summary_directory + model_summary_filename)
    
    ## Choose the sheet based on the model name
    sheet = wb.get_sheet_by_name(model_name)
    
    ## Start to write in a new line
    row_num = sheet.max_row + 1

    ## Write the model summary on specific row
    for key, value in model_summary.items():     
        if isinstance(value, float):
            sheet[str(key) + str(row_num)].value = value
        else:
            sheet[str(key) + str(row_num)].value = str(value)

    wb.save(filename=model_summary_directory+model_summary_filename) 
    print('Model summary successfully saved')

if __name__ == '__main__':
    DATE_VALUES, PRICE_VALUES, ORIGINAL_DATES = preprocess_data()
    svr_predict(DATE_VALUES, PRICE_VALUES, ORIGINAL_DATES)
    print('=================================================')

