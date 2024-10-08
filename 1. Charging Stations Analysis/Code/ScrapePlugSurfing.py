# -*- coding: utf-8 -*-
"""
Created on Tue Feb 19 10:12:48 2019

@author: EEANNNG
"""

import pandas as pd
import numpy as np
import requests
import json
import ast
import matplotlib.pyplot as plt
import pandas.io.json as pd_json 
from Utils import hasNumbers, get_country_bounding_box, get_country_code, get_country, get_providers_for_country, get_country_bounding_box_stepsize, write_dfs_to_xlsx_sheets, read_xlsx_sheets_into_dfs, get_session

#=============================================================================================
# Modify this before run
#=============================================================================================
folder = r"C:\Users\EEANNNG\WORK\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\Charging Stations Project"
#referenceExcel = folder+"/Data Reference/PlugSurfing Reference.xlsx"

def scrapePlugSurfing(country, fetchNewData):
    countryCode = get_country_code(country)  
    #=============================================================================================
    # Pull data from PlugSurfing API and store into CSV
    #=============================================================================================
    if fetchNewData==True:
        latMin,latMax,lonMin,lonMax = get_country_bounding_box(countryCode)
        jsonFile = folder+'/JSONs/PlugSurfing/'+country+'.json'
        companies_jsonFile = folder+'/JSONs/PlugSurfing/Companies.json'
        providers_file = folder+"/Data Reference/PlugSurfing_Providers.csv"
        
        # Call API to get json data
        # Get all station ID's within the bounding box
        r = get_session().get('https://api.plugsurfing.com/persik/map-charging-stations?&min-lat='+str(latMin)+'&max-lat='+str(latMax)+'&min-lon='+str(lonMin)+'&max-lon='+str(lonMax),headers={'Authorization': '88234shdfsdkl0_$1sdvRd01_233fdd'})
        chargingStationIDs_json = r.json()
        stationIDs_df = pd_json.json_normalize(chargingStationIDs_json)
        stationIDs = stationIDs_df.id.unique().tolist()
        # Get full station details for ID's above
        chargingStations_json = []
        while len(stationIDs) > 0:
            stationIDs100 = stationIDs[0:100]
            stationIDs = list(set(stationIDs).difference(set(stationIDs100)))
            r = get_session().get('https://api.plugsurfing.com/api/v4/request',headers={'Authorization': 'key=8b17b750-9466-4ed5-a16a-74df9c8107e7'},json={"station-get-by-ids": {"station-ids": stationIDs100}})
            chargingStations_json = chargingStations_json + [r.json()]
    
        # Store returned json data into json file
        with open(jsonFile, 'w') as outfile:  
            json.dump(chargingStations_json, outfile)
                
        # Read data from JSON file
        with open(jsonFile,encoding="utf-8") as json_file:  
            chargingStations_json = json.load(json_file)
    
        if len(chargingStations_json)>0:
            chargingStations_df = pd_json.json_normalize(pd_json.json_normalize(chargingStations_json).stations.apply(pd.Series).stack()).set_index('id')
            companies_df = pd_json.json_normalize(pd_json.json_normalize(chargingStations_json).companies.apply(pd.Series).stack()).drop_duplicates('id').set_index('id')
            # Add the list of companies to the previously stored CSV
            companiesAll_df = pd.read_csv(providers_file,encoding="utf8")
            companiesAll_df = pd.concat([companiesAll_df,companies_df]).drop_duplicates('id')
            companiesAll_df.to_csv(providers_file, encoding='utf_8_sig')
                
            # Save to CSVs
            print(chargingStations_df['address.country'].value_counts())
            chargingStations_df['address.country'] = [x if len(x)>3 else get_country(x) for x in chargingStations_df['address.country']]
            chargingStations_df = chargingStations_df[chargingStations_df['address.country']==country]
            chargingStations_df = chargingStations_df.drop_duplicates(['latitude','longitude'])
            chargingStations_df.to_csv(folder+"/CSVs/PlugSurfing/"+country+"_Raw.csv", encoding='utf_8_sig')
            
            connectors_df = chargingStations_df['connectors'].apply(pd.Series).stack().reset_index().set_index('id')[0].apply(pd.Series).rename(columns={'id':'connector.id'})
            connectors_df = pd.concat([connectors_df, connectors_df['prices'].apply(pd.Series)], axis=1, sort=False)
            connectors_df = pd.concat([connectors_df, connectors_df['tariff'].apply(pd.Series)], axis=1, sort=False)
            connectors_df.to_csv(folder+"/CSVs/PlugSurfing/"+country+"_Connectors_Raw.csv", encoding='utf_8_sig')
    
    #=============================================================================================
    # Enrich data
    #=============================================================================================
    # Read data from CSV    
    chargingStations_df = pd.read_csv(folder+"/CSVs/PlugSurfing/"+country+"_Raw.csv",index_col="id")
    
    # Get providers 
    # Search local providers in "operatorName", "operatorComment", "comment" columns, if not present, use the "operatorName" itself
    plugsurfing_providers = pd.read_csv(folder+"/Data Reference/PlugSurfing_Providers.csv",index_col="id")
    providers = get_providers_for_country(country)
    providers['provider'] = providers.Provider.str.lower().to_frame()
    chargingStations_df['provider'] = chargingStations_df['operator-company-id'].map(plugsurfing_providers.name)
    chargingStations_df['readable-name'] = chargingStations_df['readable-name'] if 'readable-name' in chargingStations_df.columns else ""
    chargingStations_df['local_provider'] = [", ".join(x) for i,x in chargingStations_df[['name','readable-name','notes','description','contact.web','provider']].astype(str).iterrows()]
    chargingStations_df['local_provider'] = [next(iter(list(providers.ProviderUmbrella[[ x.lower().find(y) > -1 for y in providers.provider]] )),None) for x in chargingStations_df['local_provider']]
    chargingStations_df['provider'] = [ x.local_provider if pd.notna(x.local_provider) & (x.local_provider != "") else x.provider for i, x in chargingStations_df.iterrows() ]
    
    # Get dynamic
    chargingStations_df['isDynamic'] = chargingStations_df['has-dynamic-info']
    
    # Get access
    chargingStations_df['access'] = chargingStations_df['is-private'].map({True:'private',False:'public'})
    
    # Count AC/DC connectors per station
    connectors_df = pd.read_csv(folder+"/CSVs/PlugSurfing/"+country+"_Connectors_Raw.csv",encoding="utf8",index_col="id")
    connectors_df['AC_DC'] = connectors_df['mode'].map({'Mode1':'AC','Mode2':'AC','Mode3':'AC','Mode4':'DC'})
    chargingStations_df['NrACconnectors'] = chargingStations_df.index.map(connectors_df[connectors_df.AC_DC=="AC"].groupby(connectors_df[connectors_df.AC_DC=="AC"].index)['connector.id'].count())
    chargingStations_df['NrDCconnectors'] =  chargingStations_df.index.map(connectors_df[connectors_df.AC_DC=="DC"].groupby(connectors_df[connectors_df.AC_DC=="DC"].index)['connector.id'].count())
    chargingStations_df['hasAC'] = (chargingStations_df.NrACconnectors > 0)*1
    chargingStations_df['hasDC'] = (chargingStations_df.NrDCconnectors > 0)*1
    
    # Process Address (sometimes address.streetNumber is at the end of address.street)
    chargingStations_df['address.streetNumber'] = chargingStations_df['address.streetNumber'] if 'address.streetNumber' in chargingStations_df.columns else chargingStations_df['address.street-number']
    chargingStations_df['streetNumber_strings'] = ""
    chargingStations_df['streetNumber_hasNumber'] = False
    chargingStations_df['streetNumber_strings'] = chargingStations_df['address.street'].str.split()
    chargingStations_df['streetNumber_hasNumber'] = chargingStations_df.streetNumber_strings.apply(lambda x: [i for i,y in enumerate(x) if hasNumbers(y) ])
    chargingStations_df['address.streetNumber'][pd.isna(chargingStations_df['address.streetNumber'])] = [ x[0][x[1][-1]].replace(",","") if (len(x[1])>0) else "" for i,x in chargingStations_df[['streetNumber_strings','streetNumber_hasNumber']][pd.isna(chargingStations_df['address.streetNumber'])].iterrows() ]
    chargingStations_df['address.street'] = [ x[0].replace(x[1],"") for i,x in chargingStations_df[['address.street','address.streetNumber']].iterrows() ]
    chargingStations_df['address'] = [", ".join(x) for i,x in chargingStations_df[['address.streetNumber','address.street','address.city','address.zip','address.country']].astype(str).iterrows()]
    #chargingStations_df['Postcode'] = pd.to_numeric(chargingStations_df['Postcode'], downcast = "integer", errors = "coerce" )
    
    # Add source
    chargingStations_df['source'] = "PlugSurfing"
    
    # Standardize country
    chargingStations_df = chargingStations_df[chargingStations_df['address.country']==country]
    
    #=============================================================================================
    # Save to CSV
    #=============================================================================================
    chargingStations_df.to_csv(folder+"/CSVs/PlugSurfing/"+country+"_Processed.csv", encoding='utf_8_sig')
    connectors_df.to_csv(folder+"/CSVs/PlugSurfing/"+country+"_Connectors_Processed.csv", encoding='utf_8_sig')

#=============================================================================================
# Scrape data for countries ('Turkey','Thailand','Singapore','Indonesia','Australia','New Zealand','United Arab Emirates','Russia','Japan','South Korea' dont have POIs)
#=============================================================================================
countries = ["Germany"]

for country in countries:
    scrapePlugSurfing(country,True)
