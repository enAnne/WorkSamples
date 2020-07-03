# -*- coding: utf-8 -*-
'''
Created on Sat Jul  6 09:19:42 2019

@author: EEANNNG

=========================
Data Source:
------------
OverpassTurbo query-data environment 	--> https://overpass-turbo.eu/
Tags information 			            --> https://taginfo.openstreetmap.org/

=========================
Column description:
-------------------
- "information" contains additional info for AC/DC, should get experts to look into it!!***
- "name_operator" should be taken as name

'''

import overpy
import pandas as pd
import requests
from Utils import get_country_bounding_box, get_country_code, get_providers_for_country, get_session

#=============================================================================================
# Modify this before run
#=============================================================================================
folder = r"C:\Users\EEANNNG\WORK\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\Charging Stations Project"
    
def scrapeOpenStreetMap(country, fetchNewData):
    #=============================================================================================
    # Pull data from OpenStreetMap API and GeoNames API and store into CSV
    #=============================================================================================
    if fetchNewData==True:
        countryCode = get_country_code(country,2)
        latMin,latMax,lonMin,lonMax = get_country_bounding_box(countryCode)
        node_bounding_box = ",".join([str(x) for x in [latMin,lonMin,latMax,lonMax]])
        
        # Call API 
        api = overpy.Overpass()
        result = api.query("[out:json];node['amenity'='charging_station'](" + node_bounding_box + ");out;(._;>;);out;")
        
        # Read returned data into dataframe
        chargingStations_df = pd.DataFrame()
        print("Nr POI's: ", len(result.nodes))
        i=0
        for node in result.nodes:
            i = i + 1
            print(i)
            chargingStations_temp = pd.DataFrame(node.tags,index=[0])
            chargingStations_temp['latitude'] = node.lat
            chargingStations_temp['longitude'] = node.lon
            r=get_session().get("http://api.geonames.org/countryCodeJSON?lat="+str(chargingStations_temp.latitude[0])+"&lng="+str(chargingStations_temp.longitude[0])+"&username=enanne")
            if 'countryCode' in r.json():
                chargingStations_temp['addr:country'] = r.json()['countryCode']
                chargingStations_df = pd.concat([chargingStations_temp,chargingStations_df], axis=0, ignore_index=True)
        
        # Save to CSVs
        chargingStations_df = chargingStations_df.drop_duplicates()
        chargingStations_df = chargingStations_df.drop_duplicates(['latitude','longitude'])
        print(chargingStations_df['addr:country'].value_counts())
        chargingStations_df = chargingStations_df[chargingStations_df['addr:country'] == countryCode]
        chargingStations_df.to_csv(folder+"/CSVs/OpenStreetMap/"+country+"_Raw.csv",encoding='utf_8_sig')
        
    #=============================================================================================
    # Enrich data
    #=============================================================================================
    # Read data from CSV
    chargingStations_df = pd.read_csv(folder+"/CSVs/OpenStreetMap/"+country+"_Raw.csv")
    
    # Get AC/DC
    connectorTypes = pd.read_csv(folder+r"\Data Reference\OpenStreetMap_ConnectorTypes.csv")
    connectorTypes['columnName'] = "socket:" + connectorTypes.Type
    connectorTypes['exists'] = [x in chargingStations_df.columns for x in connectorTypes.columnName]
    connectorTypes = connectorTypes[connectorTypes.exists==True]
    chargingStations_df[list(connectorTypes.columnName)] = chargingStations_df[list(connectorTypes.columnName)].fillna(0)
    AC_columns = list(connectorTypes[connectorTypes.AC_DC=="AC"].columnName)
    DC_columns = list(connectorTypes[connectorTypes.AC_DC=="DC"].columnName)
    chargingStations_df['NrACconnectors'] = chargingStations_df[AC_columns].sum(axis=1) 
    chargingStations_df['NrDCconnectors'] = chargingStations_df[DC_columns].sum(axis=1)
    if chargingStations_df['NrDCconnectors'].dtype == object :
        chargingStations_df['hasAC'] = (chargingStations_df['NrACconnectors'].str.extract('(\d+)', expand=False).astype(float)> 0)*1
    else:
        chargingStations_df['hasAC'] = (chargingStations_df['NrACconnectors']>0)*1
    
    if chargingStations_df['NrDCconnectors'].dtype == object :
        chargingStations_df['hasDC'] = (chargingStations_df['NrDCconnectors'].str.extract('(\d+)', expand=False).astype(float)> 0)*1
    else:
        chargingStations_df['hasDC'] = (chargingStations_df['NrDCconnectors']>0)*1
        
    # Get provider
    chargingStations_df['name_operator'] = [", ".join(x) for i,x in chargingStations_df[["name","operator"]].astype(str).iterrows()]
    providers = get_providers_for_country(country)
    providers['provider'] = providers.Provider.str.lower().to_frame()
    chargingStations_df['local_provider'] = [next(iter(list(providers.ProviderUmbrella[[ x.lower().find(y) > -1 for y in providers.provider]] )),None) for x in chargingStations_df['name_operator']]
    chargingStations_df['provider'] = [ x.local_provider if pd.notna(x.local_provider) & (x.local_provider != "") else x.name_operator for i, x in chargingStations_df.iterrows() ]
    
    # Add source
    chargingStations_df['source'] = "OpenStreetMap"
    
    # Standardize country
    chargingStations_df['addr:country'] = country
    
    #=============================================================================================
    # Save to CSV
    #=============================================================================================
    chargingStations_df.to_csv(folder+"/CSVs/OpenStreetMap/"+country+"_Processed.csv",encoding='utf_8_sig')

#=============================================================================================
# Scrape data for countries
#=============================================================================================
#countries = ['Australia','Romania','Slovakia','Hungary','Turkey','Thailand','Malaysia','Singapore']
countries = ['Indonesia','New Zealand','India','United Arab Emirates','Russia','South Korea','Japan']

#for country in countries:
countries = ["Brazil"]

for country in countries:
    scrapeOpenStreetMap(country,False)
