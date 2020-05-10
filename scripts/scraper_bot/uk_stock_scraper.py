# For manipulating data
import pandas as pd
import numpy as np
# For logging error and path management
import logging
import os
import os.path
# For reading and writing data from/to Gsheets, CSV, JSON and Excel
import pygsheets
import csv
import json
import openpyxl
# For text preprocessing | Regular expression
import re
import unicodedata
import string

# For parsing HTML elements to text
import requests
import urllib
from urllib.request import urlopen as uReq
import urllib.parse
from urllib.error import *
import http.client
from bs4 import BeautifulSoup
from bs4 import NavigableString as nav
# For driver setup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
# For handling selenium exception
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
# For send specific input
from selenium.webdriver.common.keys import Keys
# For handling email
import smtplib
import mimetypes
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import stdiomask
# Etc
from threading import Thread
import traceback
import pprint
import math
import calendar
import time
from itertools import islice
from datetime import datetime
import random
import ssl

print('import success')
print('=========================')

###############################################

### IMPORTANT NOTES
# 6_M -> past 6 months data
# 1_Y -> past 1 year data
# 5_Y -> past 5 years data

time_period = None
time_period_download_directory = None

### ASK THE USER FIRST WHAT'S THE TIME PERIOD FOR THE DATA IS TO BE COLLECTED
while True:
    try:
        input_time_period = str(input('What is the time period of the data you need?\n1. 6 months\n2. 1 year\n3. 5 years\nChoose (1/2/3): '))
        if input_time_period != '1' and input_time_period != '2' and input_time_period != '3':
            print('Wrong input, try again..')
            print('-------------------------')
        else:
            if input_time_period == '1':
                time_period = '6_M'
                time_period_download_directory = '6_months'
            elif input_time_period == '2':
                time_period = '1_Y'
                time_period_download_directory = '1_year'
            elif input_time_period == '3':
                time_period = '5_Y'
                time_period_download_directory = '5_years'
            break
    except Exception as err:
        print('Wrong input: ' + str(err))
        continue

### Declare main variables
main_url = 'https://uk.finance.yahoo.com'
company_names = ['Barclays plc', 'Tesco plc', 'Sainsbury plc']
stock_symbols = ['BARC', 'TSCO', 'SBRY']
lse_stock_symbols = [stock_symbol + '.L' for stock_symbol in stock_symbols]
input_time_periods = ['6_M', '1_Y', '5_Y']
script_filename = os.path.basename(__file__).replace('.py', '')
logger_filename = script_filename + ' log.log'
current_directory = os.getcwd()

## Change current directory to the 'sample' folder and save it to the downloaded directory
os.chdir('../../datasets/sample/' + time_period_download_directory)

## Determine the download directory
download_directory = os.getcwd()

### Build the driver, adding arguments
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('start-maximized')
chrome_options.add_argument('--disable_infobars')
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--allow-insecure-localhost')
chrome_options.add_argument('--ignore-ssl-errors')
chrome_options.add_argument('--allow-insecure-localhost')
chrome_options.add_argument('--disable-notifications')
chrome_options.add_argument('acceptSslCerts')
chrome_options.add_argument('acceptInsecureCerts')
# chrome_options.add_argument('--headless')
chrome_options.add_experimental_option('prefs', {'download.default_directory': download_directory})

## Change the path to the current folder path again (because the chromedriver.exe is the current folder)
os.chdir(current_directory)

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10) # Define wait variable
print('Data will be downloaded to: ' + str(download_directory))

### For writing log file
log_formatter = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_formatter)
logger = logging.getLogger(__name__)
handler = logging.FileHandler(current_directory + '\\' + logger_filename)
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter(log_formatter))
logger.addHandler(handler)

###########################################################################
###########################################################################

## Remove ASCII code, newline and carriage return
def clean_string(string):
    string = string.replace('\"', '\'\'').replace('\r', ' ').replace('\n', ' ')
    string = unicodedata.normalize('NFKD', string).encode('ascii', 'ignore')
    string = string.decode('ascii')

    return string

## Delete initial stock data to be replaced by the new one
def delete_files():
    for y in range(len(lse_stock_symbols)):
        stock_file_path = download_directory + '\\' + lse_stock_symbols[y] + '.csv'
        if os.path.exists(stock_file_path):
            os.remove(stock_file_path)
    print('All stock files removed!')
        
## Check if the stock data are downloaded successfully
def check_files():
    is_collected = True
    cnt = 0
    stock_not_collected = ''

    for x in range(len(lse_stock_symbols)):     
        if not os.path.exists(download_directory + '\\' + lse_stock_symbols[x] + '.csv'):
            is_collected = False
            cnt = cnt + 1

            if cnt == 1:
                stock_not_collected = stock_not_collected + lse_stock_symbols[x]
            else:
                stock_not_collected = stock_not_collected + ', ' + lse_stock_symbols[x]

    if is_collected == False:
        logger.info('-------------')
        logger.info('Stock: ' + stock_not_collected + ' | Download Failed')
        # logger.info('Notify me!')
        # notify_email()
    else:
        print('---------------------------------------')
        print('ALL STOCK DATA SUCCESSFULLY COLLECTED!')
        print('SAVED IN: ' + str(download_directory))

## Notify myself when the download failed
def notify_email():
    ## Email Credentials
    sender = 'ID Kevin Automation'
    personal_email = 'idkevinautomation@gmail.com'
    login_email = 'idkevinautomation@gmail.com'
    # login_password = stdiomask.getpass()
    login_password = '14c514c5'
    recipient = ['kevinkurnia13@gmail.com', 'kevinkurnia12@gmail.com']
    cc_recipient = []
    all_recipient = recipient + cc_recipient

    ## Define the email
    email_subject = "[IMPORTANT] Error in Stock Data Collection"
    email_message = '''  
            Hi Kevin, <br><br>
            There's an error in your automation -> stock_scraper.py <br>
            PLease kindly check your script. Thank you.<br>
            Best Regards, <br>
            ID Kevin Automation
            '''

    ## Compose the message
    msg_mime = MIMEMultipart()
    msg_mime['Subject'] = email_subject
    msg_mime['From'] = sender
    msg_mime['To'] = ", ".join(recipient)
    if len(cc_recipient) > 0:
        msg_mime['CC'] = ", ".join(cc_recipient)
    # msg_text = MIMEText(email_message, 'plain') # if the message format != HTML
    msg_text = MIMEText(email_message, 'html')
    msg_mime.attach(msg_text)

    ## Attachments
    attachments = []

    ## Add attachment if there's an attachment
    for file in attachments:
        try:
            with open(file, 'rb') as fp:
                msg = MIMEBase('application', "octet-stream")
                msg.set_payload(fp.read())
            encoders.encode_base64(msg) 
            msg.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file))
            msg_mime.attach(msg)
        except Exception as err:
            logger.info('Error while loading attachments: ' + str(err))
            raise

    composed_email = msg_mime.as_string()

    ## Send email
    try:
        print('\nStart sending..')
        time.sleep(2)

        smtp_obj = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_obj.ehlo()
        smtp_obj.starttls()
        smtp_obj.ehlo()
        smtp_obj.login(login_email, login_password)
        smtp_obj.sendmail(sender, all_recipient, composed_email)
        smtp_obj.close()

        print("Email successfully sent!")
        time.sleep(1)
    except Exception as err:
        logger.info('Error while sending the email: ' + str(err))
        # pass

## Main function
def main(time_period):
    try:
        random_int = random.randint(1, 3)

        print('\n-- STOCK TIME-SERIES DATA COLLECTION --\n')

        if time_period == '6_M':
            print('Time Frame setting: 6 Months')
        elif time_period == '1_Y':
            print('Time Frame setting: 1 Year')
        elif time_period == '5_Y':
            print('Time Frame setting: 5 Years')
        else:
            print('Time Frame setting (not default): ' + time_period)    

        ## Delete existing stock data
        print('Delete existing stock data!')
        delete_files()

        ## Open Yahoo Finance website
        print('GO TO YAHOO FINANCE..')
        driver.get(main_url)

        ## Click OK if there's a pop-up
        try:
            time.sleep(2)
            popup_ok_btn = driver.find_element_by_xpath("//button[@name='agree']")
            popup_ok_btn.click()
            driver.get(main_url)
        except:
            pass

        for i in range(len(lse_stock_symbols)):
            print('===========================')

            ## Search for specific stock symbol
            try:
                print('Search for ' + company_names[i] + '..')
                search_bar = wait.until(lambda driver: driver.find_element_by_xpath("//input[@id='yfin-usr-qry']"))
                search_bar.send_keys(lse_stock_symbols[i])
                time.sleep(1)
                search_btn = driver.find_element_by_xpath("//button[@id='search-button']")
                search_btn.click()
                time.sleep(1.5)
            except NoSuchElementException as err:
                print('No element found: ' + str(err))
                driver.find_element_by_css_selector('body').send_keys(Keys.ENTER)
            except Exception as err_f:
                logger.info('Error: ' + str(err_f))
            time.sleep(2)

            ## Go to historical data tab
            try: # Selenium
                print('Go to historical data tab..')
                historical_data_cat = driver.find_element_by_xpath("//li[@data-test='HISTORICAL_DATA']")
                historical_data_cat.click()
            except: # Request
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                list_cat = soup.find('div', {'id': 'quote-nav'}).find_all('li')
                historical_data_cat_url = list_cat[4].find('a', href=True)['href']
                driver.get(main_url + historical_data_cat_url)
            time.sleep(2)

            ## Configure time-period option
            try:
                print('Configure time period..')
                driver.execute_script("window.scrollTo(0, 350)")
                # try:
                #     time_period = wait.until(lambda driver: driver.find_element_by_xpath("//input[@data-test='date-picker-full-range']"))
                #     time_period.click()
                # except:
                #     pass
                # Click time period dropdown
                time.sleep(0.5)
                time_period_dropdown = wait.until(lambda driver: driver.find_element_by_xpath("//span[@class='C($linkColor) Fz(14px)']"))
                time_period_dropdown.click()
                # try:
                #     time_period_opt = driver.find_element_by_xpath("//div[@data-test='date-picker-menu']").find_element_by_xpath("//span[@data-value='{}']".format(time_period))
                #     time_period_opt.click()
                #     time.sleep(0.5)
                # except:
                #     pass
                try:
                    time.sleep(1)
                    time_period_opt = driver.find_element_by_xpath("//div[@data-test='date-picker-menu']").find_element_by_xpath("//button[@data-value='{}']".format(time_period))
                    time_period_opt.click()
                    apply_btn = driver.find_element_by_xpath("//button[@class=' Bgc($linkColor) Bdrs(3px) Px(20px) Miw(100px) Whs(nw) Fz(s) Fw(500) C(white) Bgc($linkActiveColor):h Bd(0) D(ib) Cur(p) Td(n)  Py(9px) Fl(end)']")
                    apply_btn.click()
                    time.sleep(1.5)
                except Exception as err:
                    print(err)
                    print('Failed to pick time frame period')
            except Exception as err:
                logger.info('Error: ' + str(err))
            time.sleep(2) # MUST allow time for applying the time-period configuration

            ## Download data
            try: # Selenium
                print('Download ' + lse_stock_symbols[i] + ' data..')
                download_btn = driver.find_element_by_xpath("//a[@class='Fl(end) Mt(3px) Cur(p)']")
                download_btn.click()
            except: # Request
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                download_btn = soup.find('span', class_='Fl(end) Pos(r) T(-6px)').find('a', href=True)
                download_btn_url = download_btn['href']
                driver.get(download_btn_url)
            time.sleep(3)

    except Exception as err:
        logger.info('ERROR (main()): ' + str(err))
        # print('Notify me!')
        # notify_email()  

    check_files()
    # driver.quit()

############################################################### START HERE

if __name__ == '__main__':
    logger.info('START')
    main(time_period)
    logger.info('\nEND')


