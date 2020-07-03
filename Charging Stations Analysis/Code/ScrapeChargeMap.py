# -*- coding: utf-8 -*-
"""
Created on Mon Feb 25 09:16:50 2019

@author: EEANNNG

1. Scrape the Charging stations POI address from EA-Anywhere (Thailands own charging station provider)
2. Use Google API to get the ZIP code

"""

from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary 
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities 
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import numpy as np
import requests
import urllib
import time 


#=============================================================================================
# Modify this before run
#=============================================================================================
googleAPIkey = "AIzaSyCV8uJxTzwSg_P4LT_aiAMLRsd-dfCeMoA"
newFile = "C:/Users/EEANNNG/WORK/CASE/EQ Score/eq-hot-leads-crm/Romania/Microdemographic Raw/ChargingStations.csv"
#=============================================================================================

binary = FirefoxBinary('C:\\Program Files\\Mozilla Firefox\\firefox.exe') 
caps = DesiredCapabilities().FIREFOX 
caps["marionette"] = True 
#driver = webdriver.Firefox(capabilities=caps, firefox_binary=binary, executable_path="C:\\Utility\\BrowserDrivers\\geckodriver.exe")
#driver.find_element_by_tag_name('html').send_keys(Keys.CONTROL, '0')
driver = webdriver.Firefox()
driver.get("https://chargemap.com/map") 

# Search for a country, then click on list

# Keep scrolling
for i in range(0,100):
  driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
  time.sleep(1)# 5 seconds

# Get Name
elements = driver.find_elements_by_xpath('//*[@class="itemfull-title"]/h3')
names = [x.get_attribute('innerHTML') for x in elements]

#Get address 
elements = driver.find_elements_by_xpath('//*[@class="itemfull-text"]')
address = [x.get_attribute('innerHTML') for x in elements]

# Get number charging points
parentElements = driver.find_elements_by_xpath('//*[@class="itemfull-connectors clearfix"]')
elements = [x.find_elements_by_xpath('div/div/div') for x in parentElements]
chargePoints = [ [ x.get_attribute('innerHTML') for x in y ] for y in elements ]


chargingStationData = pd.DataFrame( {'name':names,'address':address,'chargePoints':chargePoints} )
chargingStationData['address'] = chargingStationData.address.str.strip()
chargingStationData['town'] = chargingStationData.address.str.split(' - ').str[-1]
chargingStationData['town'] = chargingStationData.town.str.replace('- ','')
chargingStationData['chargePointsTotal'] = chargingStationData.chargePoints.apply( lambda connections: sum([pd.to_numeric(connection.replace('x','')) for connection in connections]) ) 

# If there is a mapping for Municipality name to Zip code file
from fuzzywuzzy import process
municipalityToZipMappingFile = "C:/Users/EEANNNG/WORK/CASE/EQ Score/eq-hot-leads-crm/Slovakia/Microdemographic Raw/Municipality to Zip Code mapping.xlsx"
municipalityToZipMap = pd.ExcelFile(municipalityToZipMappingFile).parse('Sheet1')
municipalityToZipMap.columns=['Municipality', 'Year', 'Alt', 'Zip', 'Phone']
municipalityToZipMap.set_index('Municipality',inplace=True)
chargingStationData['zip'] = chargingStationData.town.map(municipalityToZipMap.Zip)
chargingStationData['fuzzyScore'] = 0

for i in range( 4, 5 ): # range( 0, max(chargingStationData.index)+1 ):    
    if pd.isnull(chargingStationData.zip[i]):
         town, score = process.extractOne(chargingStationData.town, municipalityToZipMap.index)
         chargingStationData.zip[i]

for i in range( 0, max(chargingStationData.index)+1 ) :    
    if pd.isnull(chargingStationData.zip[i]):
        address = urllib.parse.quote_plus(chargingStationData.address[i], safe='', encoding=None, errors=None)
        url = "https://maps.googleapis.com/maps/api/geocode/json?address=" + address + "&key=" + googleAPIkey
        r = requests.get(url) 
        json_data = r.json() 
        if json_data['status'] == 'OK':
            address_components = json_data['results'][0]['address_components']
            postcode_index = [i for i, x in enumerate(address_components) if x['types']==['postal_code']]
            country_index = [i for i, x in enumerate(address_components) if 'country' in x['types']]
            #print(postcode[index[0]]['long_name'])
            if( len(postcode_index) > 0 ):
                chargingStationData.loc[i,'zip'] = address_components[postcode_index[0]]['long_name']  
            if( len(country_index) > 0 ):
                chargingStationData.loc[i,'country'] = address_components[country_index[0]]['long_name']  
            
chargingStationData.to_csv(newFile, index=False, encoding='utf_8_sig')

driver.close()

chargingStationData.to_csv('C:/Users/EEANNNG/WORK/CASE/EQ Score/eq-hot-leads-crm/Romania/Microdemographic Raw/ChargingStationsProcessing.csv', encoding='utf_8_sig')
