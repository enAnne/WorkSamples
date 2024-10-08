# -*- coding: utf-8 -*-
"""
Created on Wed Jun 19 09:49:57 2019

@author: EEANNNG

=========================
Data Source:
------------
ConnectorTypes API   --> https://ev-v2.cit.cc.api.here.com/ev/connectortypes.json?app_id=DemoCredForAutomotiveAPI&app_code=JZlojTwKtPLbrQ9fEGznlA
    
"""

import pandas as pd
import numpy as np
import requests
import random
import ast
import json
import pandas.io.json as pd_json 
from Utils import get_country_bounding_box, get_country_code, get_providers_for_country, get_country_bounding_box_stepsize, get_session

#=============================================================================================
# Modify this before run
#=============================================================================================
folder = r"C:\Users\EEANNNG\WORK\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\Charging Stations Project"
    
def scrapeHERE(country, fetchNewData):
    countryCode = get_country_code(country,2)  
    countryHERE = get_country_code(country,3) 
    #=============================================================================================
    # Pull data from HERE API and store into CSV
    #=============================================================================================
    if fetchNewData==True:
        jsonFile = folder+'/JSONs/HERE/'+country+'.json'
        latMin,latMax,lonMin,lonMax = get_country_bounding_box(countryCode)
        latShiftDegrees,lonShiftDegrees = get_country_bounding_box_stepsize(countryCode,200)
        
        # Call API and store returned json data into json file
        chargingStations_json = []
        for lon in np.arange(lonMin-lonShiftDegrees,lonMax+lonShiftDegrees,lonShiftDegrees):
            for lat in np.arange(latMin-latShiftDegrees,latMax+latShiftDegrees,latShiftDegrees):
                print(lon,lat)
                r=get_session().get("https://ev-v2.cit.cc.api.here.com/ev/stations.json?app_id=DemoCredForAutomotiveAPI&app_code=JZlojTwKtPLbrQ9fEGznlA&prox="+str(lat)+","+str(lon)+",200000&maxresults=1000")
                if (r.json()['count'] > 0) :
                    chargingStations_json = chargingStations_json + r.json()['evStations']['evStation']
        with open(jsonFile, 'w') as outfile:  
                json.dump(chargingStations_json, outfile)
                
        # Read data from JSON file
        with open(jsonFile,encoding="utf-8") as json_file:  
            chargingStations_json = json.load(json_file)
            chargingStations_df = pd_json.json_normalize(chargingStations_json)
            
        # Save to CSVs
        chargingStations_df = chargingStations_df.drop_duplicates('id')
        chargingStations_df = chargingStations_df.drop_duplicates(['position.latitude','position.longitude'])
        print(chargingStations_df['address.country'].value_counts())
        chargingStations_df = chargingStations_df[chargingStations_df['address.country']==countryHERE]
        chargingStations_df.to_csv(folder+"/CSVs/HERE/"+country+"_Raw.csv",encoding='utf_8_sig')
        
    #=============================================================================================    
    # Enrich data
    #=============================================================================================
    # Read data from CSV    
    chargingStations_df = pd.read_csv(folder+"/CSVs/HERE/"+country+"_Raw.csv",index_col=0)
    
    # Get address
    chargingStations_df['address'] = [", ".join(x) for i,x in chargingStations_df[['address.streetNumber','address.street','address.city','address.postalCode','address.region','address.country']].astype(str).iterrows()]
    
    chargingStations_df['NrACconnectors'] = 1
    chargingStations_df['NrDCconnectors'] = 0
    chargingStations_df['hasAC'] = 1
    chargingStations_df['hasDC'] = 0
    
    connectors_df = chargingStations_df['connectors.connector'].dropna().apply(ast.literal_eval)
    if connectors_df.shape[0]>0:
        connectors_df = connectors_df.apply(pd.Series).reset_index()
        connectors_df = pd.melt(connectors_df, id_vars =['index'], value_vars = connectors_df.columns[1:]).set_index('index').drop('variable',axis=1).dropna()
        connectors_df = pd.concat([connectors_df, connectors_df['value'].apply(pd.Series)],axis=1) 
        connectors_df = pd.concat([connectors_df, connectors_df['chargingPoint'].apply(pd.Series), connectors_df['connectorDetails'].apply(pd.Series), connectors_df['connectorType'].apply(pd.Series).rename(columns={'name':'connectorType_Name','id':'connectorType_Id'})],axis=1)
        connectors_df = connectors_df.drop(['value','connectorType','connectorDetails','chargingPoint'],axis=1)
        connectors_df['access'] = connectors_df['privateAccess'].map({True:'private',False:'public'})
        connectors_df = connectors_df.reset_index().rename(columns={'index':'id'})
        
        # Count AC/DC connectors per station
        connectorTypes_file = folder + r"\Data Reference\HERE_ConnectorTypes.csv"
        connectorTypes_df = pd.read_csv(connectorTypes_file,index_col=0)
        connectors_df['AC_DC'] = None
        if 'voltsRange' in connectors_df.columns:
            connectors_df['AC_DC'] = [ x if (x=="AC") | (x=="DC") else "" for x in connectors_df.voltsRange.str[-2:] ] 
        elif 'customerConnectorName' in connectors_df.columns:
            connectors_df['AC_DC'] = [ "DC" if (x.find("DC")>-1) else "AC" if (x.find("AC")>-1) else "" for x in connectors_df.customerConnectorName ] 
        connectors_df['AC_DC_derived'] = connectors_df.connectorType_Id.astype(int).map(connectorTypes_df.AC_DC)  
        connectors_df['AC_DC'] = [ x.AC_DC_derived if (x.AC_DC=="") else x.AC_DC for i,x in connectors_df.iterrows() ] 
        chargingStations_df['NrACconnectors'] = chargingStations_df.index.map(connectors_df[connectors_df.AC_DC=='AC'].groupby('id').numberOfConnectors.sum())
        chargingStations_df['NrDCconnectors'] = chargingStations_df.index.map(connectors_df[connectors_df.AC_DC=='DC'].groupby('id').numberOfConnectors.sum())
        chargingStations_df['hasAC'] = (chargingStations_df.NrACconnectors > 0)*1
        chargingStations_df['hasDC'] = (chargingStations_df.NrDCconnectors > 0)*1
    
    # Get providers 
    # Get HERE providers from "supplierName" or "manufacturer" columns
    chargingStations_df['here_provider'] = ""
    if connectors_df.shape[0]>0:
        chargingStations_df["evStationDetails.notes"] = chargingStations_df["evStationDetails.notes"] if "evStationDetails.notes" in connectors_df.columns else ""
        if 'supplierName' in connectors_df.columns:
            chargingStations_df['here_provider'] = chargingStations_df.index.map(connectors_df.groupby('id').supplierName.unique().map(lambda x: x[0]))
        elif 'manufacturer' in connectors_df.columns:
            chargingStations_df['here_provider'] = chargingStations_df.index.map(connectors_df.groupby('id').manufacturer.unique().map(lambda x: x[0]))    
    # Search local providers in "evStationDetails.notes", "name" column
    providers = get_providers_for_country(country)
    providers['provider'] = providers.Provider.str.lower().to_frame()
    chargingStations_df['local_provider'] = [", ".join(x) for i,x in chargingStations_df[['name','here_provider',]].astype(str).iterrows()]
    chargingStations_df['local_provider'] = [next(iter(list(providers.ProviderUmbrella[[ x.lower().find(y) > -1 for y in providers.provider]] )),None) if pd.notnull(x) else "" for x in chargingStations_df['local_provider']]
    chargingStations_df['provider'] = [ x.local_provider if pd.notna(x.local_provider) & (x.local_provider != "") else x.here_provider for i, x in chargingStations_df.iterrows() ]
    
    # Get access
    chargingStations_df['access'] = "public"
    if connectors_df.shape[0]>0:
        chargingStations_df['access'] = chargingStations_df.index.map(connectors_df.groupby('id').access.unique().map(lambda x: x[0]))
    
    # Add source
    chargingStations_df['source'] = "HERE"
    
    # Standardize country
    chargingStations_df['address.country'] = country
    
    #=============================================================================================
    # Save to CSV
    #=============================================================================================
    chargingStations_df.to_csv(folder+"/CSVs/HERE/"+country+"_Processed.csv",encoding='utf_8_sig')
    connectors_df.to_csv(folder+"/CSVs/HERE/"+country+"_Connectors_Processed.csv",encoding='utf_8_sig')

#=============================================================================================
# Scrape data for countries ('Japan','South Korea' dont have POIs)
#=============================================================================================
countries = ['Romania','Slovakia','Hungary','Turkey','Thailand','Malaysia','Singapore','Indonesia','Australia','New Zealand','India','United Arab Emirates','Russia']
countries = ["Australia"]
for country in countries:
    scrapeHERE(country,True)
