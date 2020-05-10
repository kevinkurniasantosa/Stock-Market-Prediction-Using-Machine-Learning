# For data manipulation
import csv
import numpy as np 
import pandas as pd 
# For plotting data
import matplotlib.pyplot as plt 
from matplotlib.pylab import rcParams
from matplotlib import style 
# For linear regression
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split 
from sklearn.preprocessing import MinMaxScaler # for normalizing data
from sklearn import metrics
from sklearn.model_selection import train_test_split
# For warnings filter
from warnings import simplefilter
# For email
import smtplib
# from email.MIMEMultipart import MIMEMultipart # For python 2
# from email.MIMEText import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import win32com.client
# For writing up in excel
import xlsxwriter
import openpyxl
# etc
import datetime
from datetime import date, timedelta
import os, os.path
import re
import time

print('import success')

### SETUP THE FIGURE SIZE FOR PLOT
rcParams['figure.figsize'] = 12,6
# rcParams['figure.figsize'] = 20,10

### TO IGNORE FUTURE WARNINGS
simplefilter(action='ignore', category=FutureWarning)

### SCALING FEATURES TO RANGE 
scaler = MinMaxScaler(feature_range=(0, 1))

### DEFINE TODAY'S DATE
today_date = date.today().strftime('%Y-%m-%d')
print('SCRIPT RUN ON ' + today_date)
print('================================\n')

########################################## CONFIGURATION REQUIRED ##########################################
### Please check/change the parameters below before running

### PERCENTAGE OF TRAINING AND TESTING DATA
train_percent = 0.8
test_percent = 0.2

### STOCK CSV DIRECTORY
time_period_directory = '5_years/'
stock_name = ['Tesco', 'Sainsbury']
csv_stock_name = ['TSCO.L.csv', 'SBRY.L.csv']
# csv_stock_name = 'TSCO.L.csv'
csv_stock_path = '../../datasets/UK Stock Data/' + time_period_directory

### STOCK COMPANY NAME
stock_symbol = [s.replace('.L.csv', '') for s in csv_stock_name]

x_variable = 'Date' # X should be the date in this case
# y_variable = 'Close'
y_variable = 'Adj Close'

### MODEL SPECIFICATIONS
model_name = 'Linear Regression'
model_summary_directory = '../.././' 
model_summary_filename = 'Model Summary.xlsx'

########################################################
########################################################

### FOR DATA PREPROCESSING (X: DATE, Y: CLOSE PRICE) | return -> data, train_data, test_data, x_train, y_train, x_test, y_test
def preprocess_data(csv_stock_path, csv_stock_name, x_variable, y_variable): 
    ################################################### DATA PREPROCESSING

    ## Convert csv file to dataframe
    df = pd.read_csv(csv_stock_path + csv_stock_name, encoding='utf-8')

    ## Remove null values
    df = df.dropna()
    df = df.reset_index()
    df = df.drop('index', axis=1)

    ## Print the first 5 rows
    print('---- INITIAL DATA ----')
    print(df)
    print('NUMBER OF DATA: ' + str(len(df)))

    ## Convert to datetime data type
    df[x_variable] = pd.to_datetime(df.Date, format='%Y-%m-%d') 
    
    ## Sort in ascending order based on Date column
    df = df.sort_index(ascending=True, axis=0)
    
    ## Initialize in new variables (these variables that are going to be used for the model)
    dates = df[x_variable]
    prices = df[y_variable]

    ## Preview the data by print dataframe head and 
    print('---- PREVIEW DATA ----')
    print('Head data:\n' + str(df.head()))
    print('Tail data:\n' + str(df.tail()))
    print('\nData size (rows, columns): ' + str(df.shape))
    print('Data types: \n' + str(df.dtypes))

    ## Creating a new dataframe (remove unnecessary column data)
    data = pd.DataFrame(index=range(0, len(df)), columns=[x_variable, y_variable])

    for i in range(0, len(df)):
        data[x_variable][i] = dates[i]
        data[y_variable][i] = prices[i]

    ## Convert Date to date format
    data[x_variable] = pd.to_datetime(data.Date, format='%Y-%m-%d')

    ## Split into train and test set
    num_total_data = int(len(data))
    num_of_train_data = int(train_percent*len(data))
    num_of_test_data = int(test_percent*len(data))
    train_data = data.iloc[:num_of_train_data]
    test_data = data.iloc[num_of_train_data:]

    ## Reset index on traing and testing data
    train_data = train_data.reset_index()
    test_data = test_data.reset_index()
    train_data = train_data.drop('index', axis=1)
    test_data = test_data.drop('index', axis=1)

    ## Print train and test data
    print('-----------------------------------')
    print('TRAIN DATA\n' + str(train_data.head()))
    print('TEST DATA\n' + str(test_data.head()))

    ## Print number of train and test data
    print('-----------------------------------')
    print('Number of TRAIN DATA: ' + str(len(train_data)))
    print('Number of TEST DATA: ' + str(len(test_data)))

    ## Initialize dependent and independent variable (x and y) for training and testing
    x_train = train_data.drop(y_variable, axis=1) # Leave the Date column
    y_train = train_data[y_variable]
    x_test = test_data.drop(y_variable, axis=1)
    y_test = test_data[y_variable]

    ## Convert date training and testing to numerical values
    for i in range(num_of_train_data):
        x_train[x_variable][i] = i

    for j in range(num_of_test_data+1):
        x_test[x_variable][j] = num_of_train_data + j

    # Preview X Train, Y Train, X Test, Y Test
    print('---------------------------------')
    print('X TRAIN:\n' + str(x_train))
    print('Y TRAIN:\n' + str(y_train))
    print('---------------------------------')
    print('X TEST:\n' + str(x_test))
    print('Y TEST:\n' + str(y_test))

    return data, train_data, test_data, x_train, y_train, x_test, y_test

## FOR PREDICTING PRICE TO EVALUATE THE LINEAR REGRESSION MODEL | return -> prediction made by linear regression
def predict_price(data, train_data, test_data, x_train, y_train, x_test, y_test, stock_name): 
    ################################################### MODEL DEVELOPMENT

    ## Define the linear regression model and start training
    print('Training model..')
    model = LinearRegression()
    model.fit(x_train, y_train)

    ## Get the Linear Regression equation
    print('---------------------------------')
    print('=== MODEL ===')
    print('INTERCEPT: ' + str(model.intercept_))
    print('COEFFICIENT: ' + str(model.coef_[0]))
    print('EQUATION: y = {0} + {1}x'.format(model.intercept_, model.coef_[0]))

    ## Make predictions on testing data
    y_pred = model.predict(x_test)

    ################################################### MODEL EVALUATION

    ## Evaluate the model using several metrics (Mean Absolute Error, Mean Squared Error, Root Mean Squared Error)
    mae = metrics.mean_absolute_error(y_test, y_pred)
    mse = metrics.mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(np.mean(np.power((np.array(y_test)-np.array(y_pred)), 2)))
    print('-------------------------------------------')
    print('MAE: %.3f' % (mae))
    print('MSE: %.3f' % (mse))
    print('RMSE: %.3f' % (rmse))
    print('===========================================')

    ################################################### MODEL VISUALIZATION

    ## Compare the result for further observation 
    result = pd.DataFrame({'Actual': y_test, 'Predicted': y_pred})
    print('=== RESULTS COMPARISON ON TESTING DATA ===')
    print(result)

    ## Plotting the actual datapoints and the result of linear regression
    print('=== PLOTTING ===')
    plt.scatter(test_data['Date'], y_test, label='Actual Value')
    plt.scatter(test_data['Date'], y_pred, color='red', label='Predicted Value')
    plt.title('{} - Linear Regression Result on Testing Data'.format(stock_name))
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.show()

    # Plotting the overall result
    plt.plot(train_data['Date'], y_train, label='Training Data')
    plt.plot(test_data['Date'], y_test, label='Testing Data')
    # plt.plot(test_data['Date'], y_pred, label='Result by Linear Regression')
    plt.title('{} Linear Regression Model Overview'.format(stock_name))
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.show()

    ###################################################

    return y_pred

## FOR NOTIFICATION BY AUTOMATING GMAIL
def send_gmail(stock_name):
    ## Email credentials
    sender = 'Kevin Santosa Automation'
    # personal_email = ''
    login_email = 'idkevinautomation@gmail.com'
    login_password = '14c514c5'
    email_subject = '[Daily Info] Stock Price for ' + stock_name[0] + ', ' + stock_name[1]
    email_message = '''  
                    Hi Kevin, <br><br>
                    Please check the result below.
                    '''
    recipient_list = ['kevinkurnia13@gmail.com', 'kevinkurnia12@gmail.com']
    cc_recipient_list = []
    all_recipient = recipient_list + cc_recipient_list

    ## Alias (if necessary)
    # from_alias = sender + ' ' + personal_email
    from_alias = sender

    ## Create mime message
    msg_mime = MIMEMultipart()
    msg_mime['Subject'] = email_subject
    msg_mime['From'] = from_alias
    msg_mime['To'] = ", ".join(recipient_list)
    if len(cc_recipient_list) > 0:
        msg_mime['CC'] = ", ".join(cc_recipient_list)
    # msg_text = MIMEText(email_message, 'plain') # If the message format is not HTML 
    msg_text = MIMEText(email_message, 'html')
    msg_mime.attach(msg_text)

    ## Attachment list (just in case if more than one)
    attachments = []
    # attachments = ['C:/Users/zenbook/Desktop/chromedriver.exe']

    ## Add attachment if there is
    for file in attachments:
        try:
            with open(file, 'rb') as fp:
                msg = MIMEBase('application', "octet-stream")
                msg.set_payload(fp.read())
            encoders.encode_base64(msg) 
            msg.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file))
            msg_mime.attach(msg)
        except Exception as err:
            print("Error while loading attachments:", err)
            raise

    composed_email = msg_mime.as_string()

    # Send email
    try:
        print('\nStart sending..')
        time.sleep(2)

        smtp_obj = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_obj.ehlo()
        smtp_obj.starttls()
        smtp_obj.ehlo()
        smtp_obj.login(login_email, login_password)
        smtp_obj.sendmail(from_alias, all_recipient, composed_email)
        smtp_obj.close()

        print("Email successfully sent!")
        time.sleep(1)
    except Exception as err:
        print('Error while sending the email:', err)
        # pass

def main():
    for x in range(len(csv_stock_name)):
        DATA, TRAIN_DATA, TEST_DATA, X_TRAIN, Y_TRAIN, X_TEST, Y_TEST = preprocess_data(csv_stock_path, csv_stock_name[x], x_variable, y_variable)
        PREDICTED_PRICE = predict_price(DATA, TRAIN_DATA, TEST_DATA, X_TRAIN, Y_TRAIN, X_TEST, Y_TEST, stock_name[x])
        print('=================================================\n')
    # send_gmail(stock_name)

########################################################

if __name__ == '__main__':
    main()

    




