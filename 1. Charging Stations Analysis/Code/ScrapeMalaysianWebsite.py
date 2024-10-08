# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
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
from Utils import read_xlsx_sheets_into_dfs, write_dfs_to_xlsx_sheets

#=============================================================================================
# Modify this before run
#=============================================================================================
folder = r"C:\Users\EEANNNG\WORK\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\Charging Stations Project\CSVs\EVStationMY"

fetchNewData=False

if fetchNewData==True:
    binary = FirefoxBinary('C:\\Program Files\\Mozilla Firefox\\firefox.exe') 
    caps = DesiredCapabilities().FIREFOX 
    caps["marionette"] = True 
    driver = webdriver.Firefox(executable_path=r'C:\Users\EEANNNG\AppData\Local\Continuum\anaconda3\pkgs\geckodriver-v0.24.0-win64\geckodriver.exe')
    
    # Get Stations Names
    driver.get("http://www.evstation.my/ev-phev-charging-station/") 
    elements = driver.find_elements_by_xpath('//*[@class="entry-content mh-clearfix"]/ul/li/a')
    state_sites = [x.get_attribute('href') for x in elements]

    connectors_df = pd.DataFrame()
    for state_site in state_sites:
        driver.get(state_site) 
        state_name = driver.find_element_by_xpath('//*/h1[@class="entry-title page-title"]')
        state_name = state_name.get_attribute('innerHTML').replace(" EV PHEV Charging Station","")
        elements = driver.find_elements_by_xpath('//*[@class="entry-content mh-clearfix"]/table/tbody/tr')
        connectors = [x.find_elements_by_xpath('td') for x in elements]
        connectors = pd.DataFrame([ [ x.get_attribute('innerHTML') for x in y ] for y in connectors]).drop(0)
        connectors['state'] = state_name
        connectors_df = pd.concat([connectors_df,connectors])
    connectors_df.columns = ["Serial","Name","MaxPower","State"]
    connectors_df["Name"] = connectors_df["Name"].str.replace("amp;","")            
    connectors_df["Name"] = connectors_df["Name"].str.replace("#1","")   
    connectors_df["Name"] = connectors_df["Name"].str.replace("#2","")   
    connectors_df["Name"] = connectors_df["Name"].str.replace("#3","")                    
    connectors_df["Name"] = connectors_df["Name"].str.replace("#4","")    
    connectors_df["Name"] = connectors_df["Name"].str.replace("#5","") 
    connectors_df["AC_DC"] = connectors_df["MaxPower"].str[:2] 
    connectors_df["NrACconnectors"] = connectors_df["AC_DC"] == "AC" 
    connectors_df["NrDCconnectors"] = connectors_df["AC_DC"] == "DC" 
    
    chargingStations_df = connectors_df.groupby("Name",as_index=False)['NrACconnectors','NrDCconnectors'].sum()
                              
    # Get Addresses
    chargingStationsDetails_df = pd.DataFrame()
    driver.get("http://www.evstation.my/ev-phev-charging-station/menara-dion/")
    isPrevious = True
    while isPrevious == True:
        name = driver.find_element_by_xpath('//*/h1[@class="entry-title"]')
        name = name.get_attribute('innerHTML')
        elements = driver.find_elements_by_xpath('//*[@class="entry-content mh-clearfix"]')
        chargingStations1 = [x.find_elements_by_xpath('div') for x in elements]
        chargingStations1 = pd.DataFrame([ [ x.get_attribute('innerHTML') for x in y ] for y in chargingStations1])
        chargingStations2 = [x.find_elements_by_xpath('p') for x in elements]
        chargingStations2 = pd.DataFrame([ [ x.get_attribute('innerHTML') for x in y ] for y in chargingStations2])
        chargingStations = pd.concat([chargingStations1,chargingStations2],axis=1)
        chargingStations.columns = [i for i,x in enumerate(chargingStations.columns)]
        chargingStations['Name'] = name
        chargingStationsDetails_df = pd.concat([chargingStationsDetails_df,chargingStations])
        prev_next_button = driver.find_element_by_xpath('//*[@id="main-content"]/nav/div/a')
        previous = prev_next_button.get_attribute('href')
        isPrevious = prev_next_button.get_attribute('rel') == "prev"
        driver.get(previous) 
    chargingStationsDetails_df.columns = ["Address","Phone","State","Name"]    
    chargingStationsDetails_df = chargingStationsDetails_df.drop_duplicates()    
    
    # Write to Excel and do fuzzy match manually to relate Address to Station Names
    write_dfs_to_xlsx_sheets([chargingStations_df,chargingStationsDetails_df], ["Stations","Details"], folder+"/Malaysia_Raw.xlsx")

# Charging stations data with address 
chargingStations_df = read_xlsx_sheets_into_dfs("Stations", folder+"/Malaysia_Raw.xlsx")
chargingStations_df['source'] = "EVstationMY"
chargingStations_df['country'] = "Malaysia"
chargingStations_df["hasAC"] = (chargingStations_df["NrACconnectors"] > 0)*1
chargingStations_df["hasDC"] = (chargingStations_df["NrDCconnectors"] > 0)*1
    
# Save to CSV
chargingStations_df.to_csv(folder+"/Malaysia_Processed.csv",encoding='utf_8_sig')
    
    
    
    
    
    
    
    
    
    
    
    
