# -*- coding: utf-8 -*-
"""
Created on Sat Aug 24 15:07:54 2019

@author: EEANNNG
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
from Utils import get_country_bounding_box, get_country_code, get_providers_for_country, get_country_bounding_box_stepsize

#=============================================================================================
# Modify this before run
#=============================================================================================
folder = r"C:\Users\EEANNNG\WORK\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\Charging Stations Project\CSVs\NZ gov"
googleAPIkey = "AIzaSyCV8uJxTzwSg_P4LT_aiAMLRsd-dfCeMoA"
country = "New Zealand"
#=============================================================================================

binary = FirefoxBinary('C:\\Program Files\\Mozilla Firefox\\firefox.exe') 
caps = DesiredCapabilities().FIREFOX 
caps["marionette"] = True 
driver = webdriver.Firefox()

# NZ gov website listing all charging stations in separate tables for each Teritory
driver.get("https://www.journeys.nzta.govt.nz/ev-chargers-list-view/") 

# Get charging stations from territory tables
names = driver.find_elements_by_xpath('//table[@class="table table--responsive"]/tbody/tr/td[@data-header="Name"]')
names = [ x.get_attribute('innerHTML').split("(")[0].strip() for x in names ]
address = driver.find_elements_by_xpath('//table[@class="table table--responsive"]/tbody/tr/td[@data-header="Address"]')
address = [ x.get_attribute('innerHTML') for x in address ]
owners = driver.find_elements_by_xpath('//table[@class="table table--responsive"]/tbody/tr/td[@data-header="Owner"]')
owners = [ x.get_attribute('innerHTML') for x in owners ]
cost = driver.find_elements_by_xpath('//table[@class="table table--responsive"]/tbody/tr/td[@data-header="Charging Costs"]')
cost = [ x.get_attribute('innerHTML') for x in cost ]
chargePoints = driver.find_elements_by_xpath('//table[@class="table table--responsive"]/tbody/tr/td[@data-header="Connectors"]') 
chargePoints = [x.find_elements_by_xpath('p') for x in chargePoints] 
chargePoints = [[ x.get_attribute('innerHTML').strip() for x in y] for y in chargePoints ]
chargePoints = [[[z.strip() for z in x.split("<br>")] for x in y] for y in chargePoints ]

chargingStations_df = pd.DataFrame({"name":names,"address":address,"provider":owners,"cost":cost,"chargePoints":chargePoints})
chargingStations_df.reset_index(inplace=True)
chargingStations_df["address"] = chargingStations_df["address"].str.replace("&amp;","&")

# Get Latitude, Longitude and address details using Google Geocode
for i in range( 0, max(chargingStations_df.index)+1 ) :    
    address = urllib.parse.quote_plus(chargingStations_df.address[i], safe='', encoding=None, errors=None)
    url = "https://maps.googleapis.com/maps/api/geocode/json?address=" + address + "&key=" + googleAPIkey
    r = requests.get(url) 
    json_data = r.json() 
    if json_data['status'] == 'OK':
        address_components = json_data['results'][0]['address_components']
        postcode_index = [i for i, x in enumerate(address_components) if 'postal_code' in x['types']]
        country_index = [i for i, x in enumerate(address_components) if 'country' in x['types']]
        state_index = [i for i, x in enumerate(address_components) if 'administrative_area_level_1' in x['types']]
        sublocality_index = [i for i, x in enumerate(address_components) if 'sublocality' in x['types']]
        locality_index = [i for i, x in enumerate(address_components) if 'locality' in x['types']]
        streetnr_index = [i for i, x in enumerate(address_components) if 'street_number' in x['types']]
        route_index = [i for i, x in enumerate(address_components) if 'route' in x['types']]
        #print(postcode[index[0]]['long_name'])
        if( len(postcode_index) > 0 ):
            chargingStations_df.loc[i,'zip'] = address_components[postcode_index[0]]['long_name']  
        if( len(country_index) > 0 ):
            chargingStations_df.loc[i,'country'] = address_components[country_index[0]]['long_name']  
        if( len(state_index) > 0 ):
            chargingStations_df.loc[i,'state'] = address_components[state_index[0]]['long_name']  
        if( len(locality_index) > 0 ):
            chargingStations_df.loc[i,'city'] = address_components[locality_index[0]]['long_name']  
        if( (len(locality_index) < 0) and (len(sublocality_index) > 0) ):
            chargingStations_df.loc[i,'city'] = address_components[sublocality_index[0]]['long_name']  
        if( len(streetnr_index) > 0 ):
            chargingStations_df.loc[i,'street_number'] = address_components[streetnr_index[0]]['long_name']  
        if( len(route_index) > 0 ):
            chargingStations_df.loc[i,'street'] = address_components[route_index[0]]['long_name']  
        chargingStations_df.loc[i,'latitude'] = json_data['results'][0]['geometry']['location']['lat']
        chargingStations_df.loc[i,'longitude'] = json_data['results'][0]['geometry']['location']['lng']

connectors_df = chargingStations_df.chargePoints.apply(pd.Series)
connectors_df = pd.concat([chargingStations_df[["index"]],connectors_df],axis=1)
connectors_df = pd.melt(connectors_df, id_vars=["index"],var_name='temp', value_name='chargePoint')
connectors_df = connectors_df.dropna(subset=['chargePoint'])
connectors_df[['connector','status']] = connectors_df.chargePoint.apply(pd.Series)
connectors_df = connectors_df.drop(columns=['temp','chargePoint'])
connectors_df['status'] = connectors_df['status'].str.replace("Status: ","")
connectors_df[['AC_DC','wattage','chargerType']] = connectors_df['connector'].str.split(",").apply(pd.Series)
connectors_df['AC_DC'] = connectors_df['AC_DC'].str.strip()
connectors_df['wattage'] = connectors_df['wattage'].str.strip()
connectors_df['chargerType'] = connectors_df['chargerType'].str.strip()

# Count AC/DC connectors per station
connectors_df['numberOfConnectors'] = 1
chargingStations_df['NrACconnectors'] = chargingStations_df.index.map(connectors_df[connectors_df.AC_DC=='AC'].groupby('index').numberOfConnectors.sum())
chargingStations_df['NrDCconnectors'] = chargingStations_df.index.map(connectors_df[connectors_df.AC_DC=='DC'].groupby('index').numberOfConnectors.sum())
chargingStations_df['hasAC'] = (chargingStations_df.NrACconnectors > 0)*1
chargingStations_df['hasDC'] = (chargingStations_df.NrDCconnectors > 0)*1

# Get providers 
# Search local providers
providers = get_providers_for_country(country)
providers['provider'] = providers.Provider.str.lower().to_frame()
chargingStations_df['nzGov_provider'] = chargingStations_df['provider']
chargingStations_df['local_provider'] = chargingStations_df['nzGov_provider']
chargingStations_df['local_provider'] = [next(iter(list(providers.ProviderUmbrella[[ x.lower().find(y) > -1 for y in providers.provider]] )),None) if pd.notnull(x) else "" for x in chargingStations_df['local_provider']]
chargingStations_df['provider'] = [ x.local_provider if pd.notna(x.local_provider) & (x.local_provider != "") else x.nzGov_provider for i, x in chargingStations_df.iterrows() ]

# Add source
chargingStations_df['source'] = "NZ gov"
    
connectors_df.to_csv(folder+"/"+country+"_Connectors_Processed.csv",encoding='utf_8_sig')     
chargingStations_df.to_csv(folder+"/"+country+"_Processed.csv",encoding='utf_8_sig')     
















