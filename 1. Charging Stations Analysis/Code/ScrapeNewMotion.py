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
    
def scrapeNewMotion(country, fetchNewData):
    countryCode = get_country_code(country)     
    #=============================================================================================
    # Pull data from NewMotion API and store into CSV
    #=============================================================================================
    if fetchNewData==True:
        latMin,latMax,lonMin,lonMax = get_country_bounding_box(countryCode)
        jsonFile = folder+'/JSONs/NewMotion/'+country+'.json'
        
        # Call API to get json data
        # Get all station ID's within the bounding box
        r = get_session().get("https://my.newmotion.com/api/map/v2/markers/"+str(lonMin)+"/"+str(lonMax)+"/"+str(latMin)+"/"+str(latMax)+"/16")
        chargingStationIDs_json = r.json()
        stationIDs_df = pd_json.json_normalize(chargingStationIDs_json)
        stationIDs = stationIDs_df.locationUid.unique().tolist()
        print("Nr stations:", len(stationIDs))
        # Get full station details for ID's above
        chargingStations_json = []
        for Id in stationIDs:
            r = get_session().get("https://my.newmotion.com/api/map/v2/locations/"+str(Id))
            chargingStations_json = chargingStations_json + [r.json()]
        
        # Store returned json data into json file
        with open(jsonFile, 'w') as outfile:  
            json.dump(chargingStations_json, outfile)
                
        # Read data from JSON file
        with open(jsonFile,encoding="utf-8") as json_file:  
            chargingStations_json = json.load(json_file)
    
        chargingStations_df = pd_json.json_normalize(chargingStations_json).set_index('uid')
        # Save to CSVs
        chargingStations_df['address.country'][pd.notna(chargingStations_df['address.country'])] = [x if len(x)>3 else get_country(x) for x in chargingStations_df['address.country'][pd.notna(chargingStations_df['address.country'])]]
        print(chargingStations_df['address.country'].value_counts())
        chargingStations_df = chargingStations_df[chargingStations_df['address.country']==country]
        chargingStations_df = chargingStations_df.drop_duplicates(['coordinates.latitude','coordinates.longitude'])
        chargingStations_df.to_csv(folder+"/CSVs/NewMotion/"+country+"_Raw.csv",encoding='utf_8_sig')
        if chargingStations_df.shape[0] > 0:
            connectors_basic_df = pd_json.json_normalize(chargingStations_json,record_path=['evses','connectors'],meta =['uid'],record_prefix='Connectors.',errors='ignore')
            connectors_tariff_df = pd.DataFrame()
            if 'Connectors.tariff' in connectors_basic_df.columns:
                connectors_tariff_df = connectors_basic_df['Connectors.tariff'].apply(pd.Series)
            connectors_props_df = connectors_basic_df['Connectors.electricalProperties'].apply(pd.Series)
            connectors_df = pd.concat([connectors_basic_df,connectors_tariff_df,connectors_props_df],axis=1,sort=False).drop(0)
            connectors_df.to_csv(folder+"/CSVs/NewMotion/"+country+"_Connectors_Raw.csv",encoding='utf_8_sig')
        
    #=============================================================================================
    # Enrich data
    #=============================================================================================
    # Read data from CSV    
    chargingStations_df = pd.read_csv(folder+"/CSVs/NewMotion/"+country+"_Raw.csv",encoding='utf_8_sig',index_col="uid")
    
    if chargingStations_df.shape[0] > 0:
        # Get providers 
        # Search local providers in "operatorName", "operatorComment", "comment" columns, if not present, use the "operatorName" itself
        providers = get_providers_for_country(country)
        providers['provider'] = providers.Provider.str.lower().to_frame()
        chargingStations_df['name'] = chargingStations_df['operatorName']
        chargingStations_df['operatorComment'] = chargingStations_df['operatorComment'] if 'operatorComment' in chargingStations_df.columns else ""
        chargingStations_df['comment'] = chargingStations_df['comment'] if 'comment' in chargingStations_df.columns else ""
        chargingStations_df['local_provider'] = [", ".join(x) for i,x in chargingStations_df[['operatorName','operatorComment','comment']].astype(str).iterrows()]
        chargingStations_df['local_provider'] = [next(iter(list(providers.ProviderUmbrella[[ x.lower().find(y) > -1 for y in providers.provider]] )),None) for x in chargingStations_df['local_provider']]
        chargingStations_df['provider'] = [ x.local_provider if pd.notna(x.local_provider) & (x.local_provider != "") else x.operatorName for i, x in chargingStations_df.iterrows() ]
        
        # Get access
        chargingStations_df['access'] = [ "public" if (x.lower().find("public")>-1) or (x=='Unspecified') else x.lower() for x in chargingStations_df['accessibility.status']]
        
        # Count AC/DC connectors per station
        connectors_df = pd.read_csv(folder+"/CSVs/NewMotion/"+country+"_Connectors_Raw.csv",encoding='utf_8_sig',index_col="uid")
        connectors_df['AC_DC'] = connectors_df.powerType.str[:2]
        chargingStations_df['NrACconnectors'] = chargingStations_df.index.map(connectors_df[connectors_df.AC_DC=="AC"].groupby(connectors_df[connectors_df.AC_DC=="AC"].index)['Connectors.uid'].count())
        chargingStations_df['NrDCconnectors'] =  chargingStations_df.index.map(connectors_df[connectors_df.AC_DC=="DC"].groupby(connectors_df[connectors_df.AC_DC=="DC"].index)['Connectors.uid'].count())
        chargingStations_df['hasAC'] = (chargingStations_df.NrACconnectors > 0)*1
        chargingStations_df['hasDC'] = (chargingStations_df.NrDCconnectors > 0)*1
        
        # Process Address (StreetNumber is at the end of streetAndNumber)
        if country == "Malaysia":
            chargingStations_df['streetNumber_strings'] = chargingStations_df['address.streetAndNumber'].str.split(",")
            chargingStations_df['name'] = [ x[0] for x in chargingStations_df['streetNumber_strings'] ]
        chargingStations_df['streetNumber_strings'] = chargingStations_df['address.streetAndNumber'].str.split()
        chargingStations_df['streetNumber_hasNumber'] = chargingStations_df.streetNumber_strings.apply(lambda x: [i for i,y in enumerate(x) if hasNumbers(y) ])
        chargingStations_df['streetNumber'] = [ x[0][x[1][-1]].replace(",","") if (len(x[1])>0) else "" for i,x in chargingStations_df[['streetNumber_strings','streetNumber_hasNumber']].iterrows() ]
        chargingStations_df['street'] = [ x[0].replace(x[1],"") for i,x in chargingStations_df[['address.streetAndNumber','streetNumber']].iterrows() ]
        chargingStations_df['address'] = [", ".join(x) for i,x in chargingStations_df[['streetNumber','street','address.streetAndNumber','address.city','address.postalCode','address.country']].astype(str).iterrows()]
        #chargingStations_df['Postcode'] = pd.to_numeric(chargingStations_df['Postcode'], downcast = "integer", errors = "coerce" )
        
        # Add source
        chargingStations_df['source'] = "NewMotion"
        
        # Standardize country
        chargingStations_df = chargingStations_df[chargingStations_df['address.country']==country]
        
        #=============================================================================================
        # Save to CSV
        #=============================================================================================
        chargingStations_df.to_csv(folder+"/CSVs/NewMotion/"+country+"_Processed.csv",encoding='utf_8_sig')
        connectors_df.to_csv(folder+"/CSVs/NewMotion/"+country+"_Connectors_Processed.csv",encoding='utf_8_sig')

#=============================================================================================
# Scrape data for countries ('Turkey','Singapore','Thailand','Indonesia','Australia','New Zealand','India' don't have any, check again)
#=============================================================================================
        
#countries = ['Romania','Slovakia','Hungary','Malaysia','United Arab Emirates','Russia']
countries = ['Germany']

for country in countries:
    scrapeNewMotion(country,True)
