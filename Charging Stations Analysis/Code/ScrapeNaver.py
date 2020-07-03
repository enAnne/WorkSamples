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
from Utils import get_session

country = "South Korea"
folder = r"C:\Users\EEANNNG\WORK\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\Charging Stations Project"
newFile = folder+"/CSVs/Naver/"+country+"_Raw.csv"

binary = FirefoxBinary('C:\\Program Files\\Mozilla Firefox\\firefox.exe') 
caps = DesiredCapabilities().FIREFOX 
caps["marionette"] = True 
#driver = webdriver.Firefox(capabilities=caps, firefox_binary=binary, executable_path="C:\\Utility\\BrowserDrivers\\geckodriver.exe")
#driver.find_element_by_tag_name('html').send_keys(Keys.CONTROL, '0')
driver = webdriver.Firefox()
driver.get("https://map.naver.com/?query=7KCE6riw7LCo7Lap7KCE7IaM&enc=b64") 
time.sleep(1) # 5 seconds

global chargingStationData
chargingStationData = pd.DataFrame(columns=['name','address','regionName','subRegionName','subSubRegionName'])

def scrape_pages(k, j, jj, regionName, subRegionName, subSubRegionName):
    global chargingStationData
    nrChargingStns = int(driver.find_element_by_xpath('/html/body/div[3]/div[2]/div[1]/div[2]/div[2]/div[1]/div[2]/div[1]/div[2]/h2/span/em').get_attribute('innerHTML')) # This number is displayed in red at the top right corner in the left panel
    print('subRegion', k, '-', j, '-', jj, ' : ', regionName, ' - ', subRegionName, ' - ', subSubRegionName, ' - ', nrChargingStns )
    nrPages = np.ceil( nrChargingStns / 10 ) - 1 # 10 stations per page, last page not needed to be clicked
    nextPage = 0
    currentPage = 0
    while currentPage < nrPages: 
        # For the first 5 pages, the 'a' tag is also for previous page '<'
        nextPage = currentPage % 5 + ( 1 if currentPage >= 5 else 0 ) 
        # Get Name and Addresses, append to chargingStationData
        elements = driver.find_elements_by_xpath('//*[@class="lsnx_det"]')
        elements_1by1 = [ ( element.find_element_by_xpath('dt/a'), element.find_element_by_xpath('dd[@class="addr"]') ) for element in elements]    
        elements_name_address = [(element[0].get_attribute('innerHTML'),element[1].get_attribute('innerHTML')) for element in elements_1by1]
        chargingStationDataTemp = pd.DataFrame(columns=['name','address'])
        chargingStationDataTemp['name'], chargingStationDataTemp['address'] = zip(*elements_name_address)
        chargingStationDataTemp['regionName'] = regionName
        chargingStationDataTemp['subRegionName'] = subRegionName
        chargingStationDataTemp['subSubRegionName'] = subSubRegionName
        chargingStationData = pd.concat([chargingStationData,chargingStationDataTemp])
        
        # Go to next page
        pages = driver.find_elements_by_xpath('//*[@class="paginate loaded"]/a')                
        print('pageNr', pages[nextPage].get_attribute('innerHTML'))
        pages[nextPage].click()
        time.sleep(1) # 5 seconds
        currentPage = currentPage+1
        
        
# Click on a region
driver.get("https://map.naver.com/?query=7KCE6riw7LCo7Lap7KCE7IaM&enc=b64") 
time.sleep(1) # 5 seconds
more = driver.find_element_by_xpath('//*[@class="spm spm_smore"]')
more.click()
time.sleep(1) # 5 seconds
regions = driver.find_elements_by_xpath('//*[@class="sa_lst _sub_region_lists"]/li/a')
nrRegions = len(regions)

for k in range ( 0, nrRegions ):
    regions = driver.find_elements_by_xpath('//*[@class="sa_lst _sub_region_lists"]/li/a')
    regionName = regions[k].get_attribute('innerHTML')
    regions[k].click()
    nrChargingStns = int(driver.find_element_by_xpath('/html/body/div[3]/div[2]/div[1]/div[2]/div[2]/div[1]/div[2]/div[1]/div[2]/h2/span/em').get_attribute('innerHTML'))
    print('region', k, ' : ', regionName, nrChargingStns )
    time.sleep(1) # 5 seconds
    
    more = driver.find_element_by_xpath('//*[@class="spm spm_smore"]')
    more.click()
    time.sleep(1) # 5 seconds
    subRegions = driver.find_elements_by_xpath('//*[@class="sa_lst _sub_region_lists"]/li/a')
    nrSubRegions = len(subRegions)            
    
    for j in range ( 0, nrSubRegions ):
        subRegionName = subRegions[j].get_attribute('innerHTML')
        subRegions[j].click()
        time.sleep(1) # 5 seconds
        nrChargingStns = int(driver.find_element_by_xpath('/html/body/div[3]/div[2]/div[1]/div[2]/div[2]/div[1]/div[2]/div[1]/div[2]/h2/span/em').get_attribute('innerHTML'))
        
        more = driver.find_element_by_xpath('//*[@class="spm spm_smore"]')
        more.click()
        time.sleep(1) # 5 seconds
        subSubRegions = driver.find_elements_by_xpath('//*[@class="sa_lst _sub_region_lists"]/li/a')
        nrSubSubRegions = len(subSubRegions)    
        
        if nrSubSubRegions == 1:
            scrape_pages(k, j, 0, regionName, subRegionName, subRegionName)  
        else:
            for jj in range ( 0, nrSubSubRegions ):
                subSubRegionName = subSubRegions[jj].get_attribute('innerHTML')
                subSubRegions[jj].click()
                time.sleep(1) # 5 seconds
        
                scrape_pages(k, j, jj, regionName, subRegionName, subSubRegionName)            
                    
                more = driver.find_element_by_xpath('//*[@class="spm spm_smore"]')
                more.click()
                time.sleep(1) # 5 seconds
                subRegion = driver.find_elements_by_xpath('//*[@class="sa_history"]/a')
                subRegion[1].click()
                time.sleep(1) # 5 seconds
                more = driver.find_element_by_xpath('//*[@class="spm spm_smore"]')
                more.click()
                time.sleep(1) # 5 seconds
                subSubRegions = driver.find_elements_by_xpath('//*[@class="sa_lst _sub_region_lists"]/li/a')
            
        more = driver.find_element_by_xpath('//*[@class="spm spm_smore_close"]')
        try:
            more.click()
        except:
            pass
        more = driver.find_element_by_xpath('//*[@class="spm spm_smore"]')
        more.click()
        time.sleep(1) # 5 seconds
        region = driver.find_element_by_xpath('//*[@class="sa_history"]/a')
        region.click()
        time.sleep(1) # 5 seconds
        more = driver.find_element_by_xpath('//*[@class="spm spm_smore"]')
        more.click()
        time.sleep(1) # 5 seconds
        subRegions = driver.find_elements_by_xpath('//*[@class="sa_lst _sub_region_lists"]/li/a')
    
    driver.refresh()
    time.sleep(1)
    more = driver.find_element_by_xpath('//*[@class="spm spm_smore"]')
    more.click()
    time.sleep(1) # 5 seconds

chargingStationData['zip'] = np.nan
chargingStationData['chargePointsTotal'] = 1

chargingStationData.to_csv(newFile, index=False, encoding='utf_8_sig')

driver.close()


#=============================================================================================    
# Enrich data
#=============================================================================================
# Read data from CSV    
chargingStations_df = pd.read_csv(folder+"/CSVs/Naver/"+country+"_Raw.csv")
chargingStations_df = chargingStations_df.drop_duplicates(subset=['address'])
chargingStations_df = chargingStations_df.reset_index()
#header_list = ['roadAddress','jibunAddress','englishAddress','addressElements','x','y','distance','code','BUILDING_NAME','BUILDING_NUMBER', 'DONGMYUN','LAND_NUMBER','POSTAL_CODE','RI','ROAD_NAME','SIDO','SIGUGUN']
#chargingStations_df = chargingStations_df.reindex(columns = chargingStations_df.columns.tolist() + header_list)
address_df = pd.DataFrame()

for i,row in chargingStations_df.iterrows():
    r=get_session().get("https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode?query="+row['address'], headers={"X-NCP-APIGW-API-KEY-ID":"vy3q40uerv","X-NCP-APIGW-API-KEY":"PxWfyfxteW6nnux9WSmDM9GV5ou8vHbVD95LW0nF"})
    print(i)
    if(len(r.json()['addresses'])>0):
        address = pd.DataFrame(r.json()['addresses'][0])[0:1]
        address_details = pd.DataFrame(r.json()['addresses'][0]['addressElements'])
        address_details['types'] = [x[0] for x in address_details['types']]
        address_details = address_details.pivot(index='code', columns='types', values='longName').reset_index()
        address = pd.concat([address,address_details],axis=1)
        address['address']=row['address']
        address_df = pd.concat([address_df,address])
    
chargingStations_df = pd.merge(chargingStations_df,address_df,on='address',how='left')
    
# Add source
chargingStations_df['source'] = "Naver"

# Standardize country
chargingStations_df['country'] = country

chargingStations_df = chargingStations_df.replace("",np.nan)
newFile = folder+"/CSVs/Naver/"+country+"_Processed.csv"
chargingStations_df.to_csv(newFile, index=False, encoding='utf_8_sig')
    
    
















