# For data manipulation
import pandas as pd
import numpy as np
from pandas_datareader import data
# For read data from local file system
import os 
import random
import sys 
# For plotting
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.pylab import rcParams
from matplotlib import style
# For filtering warnings
from warnings import simplefilter
# For model evaluation
from sklearn import metrics
# For building the LSTM model
import keras
from keras.callbacks import LambdaCallback
from keras.models import Sequential 
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Dropout
from keras.layers import Activation
from keras.optimizers import RMSprop
import tensorflow as tf 
# For normalizing data
from sklearn.preprocessing import MinMaxScaler
# For writing up in excel
import xlsxwriter
import openpyxl
# Etc
import datetime
from datetime import date, timedelta
import re
import time
import pickle
from keras.models import load_model

print('import success')

### SETUP THE FIGURE SIZE FOR PLOT
rcParams['figure.figsize'] = 12,6

### TO IGNORE FUTURE WARNINGS
simplefilter(action='ignore', category=FutureWarning)

### DEFINE TODAY'S DATE 
today_date = date.today().strftime('%Y-%m-%d')
print('SCRIPT RUN ON ' + today_date)
print('================================')

###################################
########################################## CONFIGURATION REQUIRED ##########################################
### Please check/change the parameters below before running

### FILE DIRECTORY CONFIGURATION
time_period_directory = '1_year/'
stock_name = 'Sainsbury'
# csv_stock_name = ['TSCO.L.csv', 'SBRY.L.csv']
csv_stock_name = 'SBRY.L.CSV'
csv_filepath = '../../datasets/UK Stock Data/' + time_period_directory

### SAVE TIME PERIOD IN NEW VARIABLE
x = re.match("(.+)_(.+)/", str(time_period_directory))
time_period = str(x.group(1)) + ' ' + str(x.group(2))

### DEFINE THE FEATURE
feature = 'Close Price'

### PERCENTAGE OF TRAINING AND TESTING DATA
train_percent = 0.8
test_percent = 0.2

### NUMBER OF TIMESTEPS
timesteps = 20

### MODEL SPECIFICATIONS
model_filename = 'lstm.pkl'
model_name = 'LSTM'
model_summary_directory = '../.././' 
model_summary_filename = 'Model Summary.xlsx'

########################################################
########################################################

## APPLY NORMALIZATION TO THE DATA
def normalize_data(train, test):
    ## Now define a scaler to normalize the data. MinMaxScalar scales all the data to be in the region of 0 and 1. And then reshape the training 
    ## and test data to be in the shape [data_size, num_features]

    ## Define scaler for normalizing the data (shrinking the range of the values into 0 to 1)
    scaler = MinMaxScaler(feature_range=(0,1))

    train = np.array(train).reshape(len(train),1)
    test = np.array(test).reshape(len(test),1)

    scaler.fit(train)
    train = scaler.transform(train)
    test = scaler.transform(test)

    print('== PREVIEW DATA AFTER NORMALIZATION ==')
    print('Train data (after normalization):\n' + str([train[x] for x in range(0,5)]))
    print('----------------------------')
    print('Test data (after normalization):\n' + str([test[x] for x in range(0,5)]))
    print('----------------------------')

    return scaler, train, test                                  

## FOR SPLITTING DATASET INTO TRAIN SET AND TEST SET
def split_dataset(dataframe):
    ## Split into train and test set
    num_total_data = int(len(dataframe))
    num_of_train_data = int(train_percent*len(dataframe))
    num_of_test_data = int(test_percent*len(dataframe))
    train_data = dataframe.iloc[:num_of_train_data]
    test_data = dataframe.iloc[num_of_train_data:]

    ## Check train and test data
    print('TRAIN DATA\n' + str(train_data.head()))
    print('TEST DATA\n' + str(test_data.tail()))

    ## Check number of train and test data
    print('-----------------------------------')
    print('Number of TRAIN DATA: ' + str(len(train_data)))
    print('Number of TEST DATA: ' + str(len(test_data)))

    return train_data, test_data

## FOR SPLITTING SEQUENCE BASED ON THE NUMBER OF TIMESTEPS TO FEED INTO THE LSTM MODEL
def split_sequences(sequences, n_steps): # Number of steps: 20 - define first in the initialization phase
    data_1 = []
    data_2 = []

    for i in range(n_steps, len(sequences)): # 20-100, for example is the number of sequence is 100
        a = sequences[i-n_steps:i, 0] # 0:20, 1:21, 2:22, ... 80:100
        b = sequences[i, 0] # 20, 21, 22, ... 100
        data_1.append(a) 
        data_2.append(b) 

    return data_1, data_2

## FOR MODEL EVALUATION
def evaluate_model(actuals, predictions):
    ## Evaluate the LSTM model using several metrics (Mean Absolute Error, Mean Absolute Percentage Error, Root Mean Squared Error)    
    mae = metrics.mean_absolute_error(actuals, predictions)
    mape = np.mean(np.abs((np.array(actuals) - np.array(predictions)) / np.array(actuals))) * 100
    mse = metrics.mean_squared_error(actuals, predictions)
    rmse = np.sqrt(mse)

    return mae, mape, rmse

## FOR VISUALIZING THE RESULTS
def visualize_results(updated_train_date, updated_test_date, full_test_date, test_data, y_train, y_org, y_pred):
    print('== VISUALIZE ACTUAL RESULTS vs. PREDICTED RESULTS ==')

    ## Visualize the actual result and the predicted result by LSTM model
    plt.plot(updated_test_date, y_org, color='blue', label='Real {} Stock Price'.format(stock_name))
    plt.plot(updated_test_date, y_pred, color='red', label='Predicted {} Stock Price'.format(stock_name))
    plt.title('{} Stock Price Prediction'.format(stock_name))
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.show()

    ## Visualize the overall data
    plt.plot(updated_train_date, y_train, color='blue', label='Train Data')
    plt.plot(full_test_date, test_data, color='steelblue', label='Test Data')
    plt.plot(updated_test_date, y_org, color='red', label='Actual Price')
    plt.scatter(updated_test_date, y_pred, color='green', label='Predicted Price')
    plt.title('LSTM | {} Stock Prices Prediction'.format(stock_name))
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()   
    plt.show()

## FOR DATA PREPARATION
def prepare_data():
    ################################################### DATA PREPROCESSING

    # Read csv file
    df = pd.read_csv(csv_filepath + csv_stock_name)

    ## Remove null values
    df = df.dropna()
    df = df.reset_index()
    df = df.drop('index', axis=1)

    ## Sort by Date
    df = df.sort_values('Date')

    ## Set the index to Date
    df.reset_index(inplace=True)
    df['Date'] = pd.to_datetime(df.Date, format='%Y-%m-%d')
    df.set_index('Date', inplace=True)
    df = df.drop('index', axis=1)

    ## Check the initial data
    print('== PREVIEW INITIAL DATA ==')
    print('Head data:\n' + str(df.head()))
    print('----------------------------')
    print('Tail data:\n' + str(df.tail()))
    print('----------------------------')
    print('NUMBER OF DATA: ' + str(len(df)))
    print('----------------------------')

    ## Create a new variable called data
    data = df.copy()

    ## Plotting initial data
    plt.plot(df['Close'])
    plt.title('{} Close Price Preview'.format(stock_name))
    plt.xlabel('Date')
    plt.ylabel('Close Price')
    plt.show()

    ## Split datasets into train and test set
    train, test = split_dataset(data)

    ## Store the original dates for plotting the predictions
    train_original_date = train.index.values
    test_original_date = test.index.values

    ## Specify train and test data
    train = train['Close']
    test = test['Close']

    ## Normalize the data
    scaler, train, test = normalize_data(train, test)

    return scaler, train, test, train_original_date, test_original_date

## FOR BUILDING THE LSTM MODEL
def build_lstm_model(scaler, train_data, test_data, train_date, test_date):
    ## Split train and test data
    x_train, y_train = split_sequences(train_data, timesteps)
    x_test, y_test = split_sequences(test_data, timesteps)

    ### Prepare train data for fitting the model
    ## Convert to numpy array
    x_train = np.array(x_train)
    y_train = np.array(y_train)

    ## Reshape x train to feed into the LSTM model: rows, timesteps, number of features
    x_train = np.reshape(x_train, (x_train.shape[0], timesteps, 1))
    print('== PREVIEW TRAIN DATA FOR FITTING LSTM MODEL ==')
    print('X_train shape: ' + str(x_train.shape))
    print('Y_train shape: ' + str(y_train.shape))
    print('X_train:\n' + str(scaler.inverse_transform(x_train[0]))) 
    print('Y_train:\n' + str(scaler.inverse_transform(y_train[0].reshape(-1,1))))

    ################################################### MODEL DEVELOPMENT

    ####### CONFIGURE DIFFERENT HYPERPARAMATERS TO FIND THE BEST LSTM MODEL
    ## 1. Change the number of neurons (100, 256)
    ## 2. Change the number of layers: 2 or 3 layers
    ## 3. Change batch size: 1, 2, 4 
    ## 4. Change dropout rate: 0.2, 0.4
    ## 5. Change the number of epochs: 250, 500, 1000

    #### Define parameters: 
    ## Number of nodes: number of units of one layer to feed into the LSTM model
    ## Dropout: the dropout rate 
    ## Batch: the total number of sample 
    ## Epochs: the number of iterations when it's passed
    ## Optimizer: the optimization algorithm
    params = {
        'n_nodes': 100, # 100, 256
        'dropout_rate': 0.2,
        'optimizer': 'RMSprop', # Adam, RMSprop
        'epochs': 100, # 20, 100, 250, 500, 1000
        'batch_size': 32 # 1, 2, 4, 64, 100, 150
    }
    # {'n_nodes': 100, 'dropout_rate': 0.2, 'optimizer': 'RMSprop', 'epochs': 100, 'batch_size': 32}


    ## Build the LSTM model
    model = keras.Sequential()

    model.add(LSTM(units=params['n_nodes'], return_sequences=True, input_shape=(timesteps, 1)))
    model.add(Dropout(params['dropout_rate']))

    model.add(LSTM(units=params['n_nodes'], return_sequences=False))
    model.add(Dropout(params['dropout_rate']))

    ## Output layer
    model.add(Dense(units=1))
    model.add(Activation('linear'))

    ## Compile the model
    
    model.compile(optimizer=params['optimizer'], loss='mean_squared_error')
    
    ## Print the architecture of the model
    print('== Model Summary ==')
    print(model.summary())

    ## Fitting the model with training set
    start = time.time()
    # model.fit(x_train, y_train, epochs=params['epochs'], batch_size=params['batch_size'])
    model_fit = model.fit(x_train, y_train, epochs=params['epochs'], batch_size=params['batch_size'], validation_split=.2)
    print('Training time: ' + str(time.time() - start) + ' seconds')

    ## Plotting train & validation loss values
    plt.plot(model_fit.history['loss'])
    plt.plot(model_fit.history['val_loss'])
    plt.title('Model loss')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Validation'], loc='upper right')
    plt.show()

    ################################################### MAKE PREDICTION

    ## Store the original test values for plotting the predictions
    y_test = np.array(y_test).reshape(len(y_test),1)
    original_y_test = scaler.inverse_transform(y_test)
    x_test = np.array(x_test)
    y_test = np.array(y_test)

    ## Reshape x_test to be predicted by the LSTM model: rows, timesteps, number of features
    x_test = np.reshape(x_test, (x_test.shape[0], timesteps, 1))
    print('== PREVIEW TEST DATA BEFORE PREDICTED BEFORE LSTM MODEL ==')
    print('X_test shape: ' + str(x_test.shape))
    print('Y_test shape: ' + str(y_test.shape))
    print('X_test:\n' + str(scaler.inverse_transform(x_test[0]))) 
    print('Y_test:\n' + str(scaler.inverse_transform(y_test[0].reshape(-1,1))))

    ## Predict the prices with the model
    y_pred = model.predict(x_test)
    y_pred = scaler.inverse_transform(y_pred)

    ################################################### MODEL EVALUATION

    ## Call evaluate_model function
    mae, mape, rmse = evaluate_model(original_y_test, y_pred)

    print('== LSTM MODEL - PERFORMANCE REPORT ==')
    print('MAE: %.3f' % (mae))
    print('MAPE: %.3f' % (mape))
    print('RMSE: %.3f' % (rmse))
    print('===========================================')

    ################################################### RESULTS VISUALIZATION

    ## Inverse transform y_train and test_data for plotting
    y_train = np.array(y_train).reshape(len(y_train),1)
    y_train = scaler.inverse_transform(y_train)
    test_data = np.array(test_data).reshape(len(test_data),1)
    test_data = scaler.inverse_transform(test_data)

    ## Update the original date based on the timesteps for visualization
    updated_train_date = []
    for i in range(timesteps, len(train_date)): 
        updated_train_date.append(train_date[i]) 

    updated_test_date = []
    for i in range(timesteps, len(test_date)): 
        updated_test_date.append(test_date[i])

    ## Call the visualize_results function to visualize the results made by 
    visualize_results(updated_train_date, updated_test_date, test_date, test_data, y_train, original_y_test, y_pred)

    print(str(params))

    ## SAVE THE MODEL SUMMARY IN EXCEL FILE
    save_model_summary(stock_name, time_period, feature, params, mae, mape, rmse)

    input_to_save_model = str(input('Do you want to save the model (Y/N)? '))
    if input_to_save_model.lower() == 'y':
        pickle.dump(model, open(model_filename, 'wb'))
        # model.save(model_filename)
        print('LSTM model is saved successfully')
        
    #################################

def lstm_predict(scaler, train_data, test_data, train_date, test_date):
    loaded_model = pickle.load(open(model_filename, 'rb'))

    ## Split train and test data
    x_train, y_train = split_sequences(train_data, timesteps)
    x_test, y_test = split_sequences(test_data, timesteps)

    ### Prepare train data for fitting the model
    ## Convert to numpy array
    x_train = np.array(x_train)
    y_train = np.array(y_train)

    ## Reshape x train to feed into the LSTM model: rows, timesteps, number of features
    x_train = np.reshape(x_train, (x_train.shape[0], timesteps, 1))

    ################################################### MAKE PREDICTION

    ## Store the original test values for plotting the predictions
    y_test = np.array(y_test).reshape(len(y_test),1)
    original_y_test = scaler.inverse_transform(y_test)                                                                              

    x_test = np.array(x_test)
    y_test = np.array(y_test)

    ## Reshape x_test to be predicted by the LSTM model: rows, timesteps, number of features
    x_test = np.reshape(x_test, (x_test.shape[0], timesteps, 1))
    print('== PREVIEW TEST DATA BEFORE PREDICTED BEFORE LSTM MODEL ==')
    print('X_test shape: ' + str(x_test.shape))
    print('Y_test shape: ' + str(y_test.shape))
    print('X_test:\n' + str(scaler.inverse_transform(x_test[0]))) 
    print('Y_test:\n' + str(scaler.inverse_transform(y_test[0].reshape(-1,1))))

    ## Predict the prices with the model
    y_pred = loaded_model.predict(x_test)
    y_pred = scaler.inverse_transform(y_pred)

    mae, mape, rmse = evaluate_model(original_y_test, y_pred)

    print('== LSTM MODEL - PERFORMANCE REPORT ==')
    print('MAE: %.3f' % (mae))
    print('MAPE: %.3f' % (mape))
    print('RMSE: %.3f' % (rmse))
    print('===========================================')

    ################################################### RESULTS VISUALIZATION

    ## Inverse transform y_train and test_data for plotting
    y_train = np.array(y_train).reshape(len(y_train),1)
    y_train = scaler.inverse_transform(y_train)
    test_data = np.array(test_data).reshape(len(test_data),1)
    test_data = scaler.inverse_transform(test_data)

    ## Update the original date based on the timesteps for visualization
    updated_train_date = []
    for i in range(timesteps, len(train_date)): 
        updated_train_date.append(train_date[i]) 

    updated_test_date = []
    for i in range(timesteps, len(test_date)): 
        updated_test_date.append(test_date[i])

    ## Call the visualize_results function to visualize the results made by 
    visualize_results(updated_train_date, updated_test_date, test_date, test_data, y_train, original_y_test, y_pred)

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
        if isinstance(value, float):
            sheet[str(key) + str(row_num)].value = value
        else:
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

    SCALER, TRAIN_DATA, TEST_DATA, TRAIN_DATE, TEST_DATE = prepare_data()

    print('------------------------------')
    if use_saved_model == False:
        build_lstm_model(SCALER, TRAIN_DATA, TEST_DATA, TRAIN_DATE, TEST_DATE)
    elif use_saved_model == True:
        print('Load the ARIMA model..')   
        lstm_predict(SCALER, TRAIN_DATA, TEST_DATA, TRAIN_DATE, TEST_DATE)

    # SCALER, TRAIN_DATA, TEST_DATA, TRAIN_DATE, TEST_DATE = prepare_data()
    # build_lstm_model(SCALER, TRAIN_DATA, TEST_DATA, TRAIN_DATE, TEST_DATE)
    
if __name__ == '__main__':
    main()







