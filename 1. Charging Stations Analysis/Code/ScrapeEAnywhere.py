# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 13:33:57 2019

@author: EEANNNG

Scrape data using Postman and save json files. 
Break into 3 parts because max display only 200 stations.

Part 1: 110 stations
https://www.eaanywhere.com/webservices/stations?zoom=11&lang=en&ne_lat=13.7&ne_lon=106&sw_lat=5&sw_lon=97

Part 2: 171 stations
https://www.eaanywhere.com/webservices/stations?zoom=11&lang=en&ne_lat=14&ne_lon=106&sw_lat=13.7&sw_lon=97

Part 3: 73 stations
https://www.eaanywhere.com/webservices/stations?zoom=11&lang=en&ne_lat=21&ne_lon=106&sw_lat=14&sw_lon=97

"""

import pandas as pd
import os
import json
import pandas.io.json as pd_json 
from Utils import search_exact_string_in_DF

folder = r"C:\Users\EEANNNG\WORK\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\Charging Stations Project"
json_folder = folder+"/JSONs/EAnywhere/"
country = "Thailand"
chargingStations_df = pd.DataFrame()
for jsonFile in os.listdir(json_folder):
    if jsonFile.startswith(country):
        with open(folder+"/JSONs/EAnywhere/"+jsonFile,encoding="utf_8_sig") as json_file:  
            chargingStations_json = json.load(json_file)
            chargingStations_df = pd.concat([chargingStations_df, pd_json.json_normalize(chargingStations_json['data'])])

chargingStations_df = chargingStations_df.set_index('id')
chargingStations_df = chargingStations_df.drop_duplicates(['latitude','longitude'])
connectors_df = chargingStations_df['list_connector'].apply(pd.Series).stack().reset_index().set_index('id')[0].apply(pd.Series)

chargingStations_df['NrACconnectors'] = chargingStations_df.index.map( connectors_df[connectors_df.charger_type_name=="AC"].groupby(connectors_df[connectors_df.charger_type_name=="AC"].index).total_connector.sum())
chargingStations_df['NrDCconnectors'] = chargingStations_df.index.map( connectors_df[connectors_df.charger_type_name=="DC"].groupby(connectors_df[connectors_df.charger_type_name=="DC"].index).total_connector.sum())
chargingStations_df['hasAC'] = (chargingStations_df.NrACconnectors > 0)*1
chargingStations_df['hasDC'] = (chargingStations_df.NrDCconnectors > 0)*1

chargingStations_df['country'] = 'Thailand'
chargingStations_df['access'] = chargingStations_df['status']
chargingStations_df['access'][chargingStations_df['access']=='Open'] = 'public'
chargingStations_df['source'] = 'EAnywhere'
chargingStations_df['provider'] = 'EAnywhere'

chargingStations_df['postalCode'] = chargingStations_df.address.str.split(', ').str[-1]
chargingStations_df['city'] = chargingStations_df.address.str.split(', ').str[-3]
chargingStations_df['street'] = chargingStations_df.address.str.split(', ').str[-5]
chargingStations_df['streetNumber'] = chargingStations_df.address.str.split(', ').str[0].str.split(' ').str[0]

chargingStations_connectors_df = pd.merge(connectors_df,chargingStations_df,left_on=connectors_df.index,right_on=chargingStations_df.index,how='outer')

chargingStations_df.to_csv(folder+"/CSVs/EAnywhere/"+country+"_Processed.csv",encoding='utf_8_sig')
connectors_df.to_csv(folder+"/CSVs/EAnywhere/"+country+"_Connectors_Processed.csv",encoding='utf_8_sig')
chargingStations_connectors_df.to_csv(folder+"/CSVs/EAnywhere/"+country+"_Stations_Connectors_Processed.csv",encoding='utf_8_sig')
