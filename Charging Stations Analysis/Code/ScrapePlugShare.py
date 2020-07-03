# -*- coding: utf-8 -*-
"""
Created on Tue Jun 11 15:58:45 2019

@author: EEANNNG

=========================
Data Source:
------------
API info    --> https://developer.plugshare.com/docs/

=========================
Column description:
-------------------
- "score" indicates how good is the data for this charging POI (0-10)
- "name_operator" should be taken as name

"""

import pandas.io.json as pd_json 
import pandas as pd
import numpy as np
import requests
import json
import ast
import pylab as pl
from Utils import get_country_bounding_box, get_country_code, get_providers_for_country, get_country_bounding_box_stepsize, get_session

#=============================================================================================
# Modify this before run
#=============================================================================================
folder = r"C:\Users\EEANNNG\WORK\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\Charging Stations Project"
isAccurate = False

def scrapePlugShare(country, fetchNewData):
countryCode = get_country_code(country,2)     
    #=============================================================================================
    # Pull data from PlugShare API and store into CSV
    #=============================================================================================
    if fetchNewData==True:
        accurate_jsonFile = folder+'/JSONs/PlugShare/'+country+('_Accurate.json' if isAccurate==True else '_Rough.json')
        latMin,latMax,lonMin,lonMax = get_country_bounding_box(countryCode)
        spanLat = latMax - latMin
        spanLon = lonMax - lonMin
        latShiftDegrees,lonShiftDegrees = get_country_bounding_box_stepsize(countryCode,200)
        
        # Call API and store returned json data into json file
        if isAccurate==True:
            chargingStations_json = []
            for lon in np.arange(lonMin-lonShiftDegrees,lonMax+lonShiftDegrees,lonShiftDegrees):
                for lat in np.arange(latMin-latShiftDegrees,latMax+latShiftDegrees,latShiftDegrees):
                    print(lat,lon)
                    r=get_session().get("https://api.plugshare.com/v3/locations/region?spanLat="+str(spanLat)+"&spanLng="+str(spanLon)+"&latitude="+str(lat)+"&longitude="+str(lon)+"&minimal=1&count=500", headers={"Authorization":"Basic d2ViX3YyOkVOanNuUE54NHhXeHVkODU="})
                    if (len(r.json())>0) :
                        chargingStations_json = r.json() + chargingStations_json
            with open(accurate_jsonFile, 'w') as outfile:  
                json.dump(chargingStations_json, outfile)
            
        else:
            response = True
            chargingStations_json = []
            i = 0
            while response == True:
                i = i+1
                r=get_session().get("https://api.plugshare.com/v3/locations/search?count=500&query="+country+"&page="+str(i), headers={"Authorization":"Basic d2ViX3YyOkVOanNuUE54NHhXeHVkODU="})
                chargingStations_json = r.json() + chargingStations_json
                response = len(r.json())>0
            with open(accurate_jsonFile, 'w') as outfile:  
                json.dump(chargingStations_json, outfile)
                    
        # Read data from JSON file 
        with open(accurate_jsonFile,encoding="utf_8_sig") as json_file:  
            chargingStations_json = json.load(json_file)
            chargingStations_df = pd_json.json_normalize(chargingStations_json)
            connectors_df = pd_json.json_normalize(chargingStations_json,record_path=['stations','outlets'],meta =['id','cost_description'],record_prefix='outlets.') 
        
        if isAccurate == True:
            #cc = countries.CountryChecker('TM_WORLD_BORDERS-0.3.shp')
            chargingStations_df['reverse_geocoded_address_components.country_code']=""
            for i,x in chargingStations_df.iterrows():
                lat = x.latitude
                lon = x.longitude
                #chargingStations_df.loc[i,'reverse_geocoded_address_components.country_code'] =  = cc.getCountry(countries.Point(49.7821, 3.5708)).iso
                r=requests.get("http://api.geonames.org/countryCodeJSON?lat="+str(lat)+"&lng="+str(lon)+"&username=enanne")
                if 'countryCode' in r.json():
                    chargingStations_df.loc[i,'reverse_geocoded_address_components.country_code'] = r.json()['countryCode']
        
        # Save to CSVs
        chargingStations_df = chargingStations_df.drop_duplicates('id')
        chargingStations_df = chargingStations_df.drop_duplicates(['latitude','longitude'])
        chargingStations_df = chargingStations_df[chargingStations_df['reverse_geocoded_address_components.country_code']==countryCode]   
        chargingStations_df.to_csv(folder+"/CSVs/PlugShare/"+country+"_Raw.csv",encoding='utf_8_sig')
        connectors_df.to_csv(folder+"/CSVs/PlugShare/"+country+"_Connectors_Raw.csv",encoding='utf_8_sig')
    
    #=============================================================================================
    # Enrich data
    #=============================================================================================
    # Read data from CSV    
    chargingStations_df = pd.read_csv(folder+"/CSVs/PlugShare/"+country+"_Raw.csv")
    chargingStations_df.rename(columns={'reverse_geocoded_address_components.country_code':'country','reverse_geocoded_address':'address','reverse_geocoded_address_components.postal_code':'postalCode','reverse_geocoded_address_components.locality':'city','reverse_geocoded_address_components.street_number':'streetNumber','reverse_geocoded_address_components.route':'street'}, inplace=True)
    
    # Check score distribution
    if "score" in chargingStations_df.columns:
        chargingStations_df.score.hist()
        nrNA = np.ceil(pd.isna(chargingStations_df.score).sum()/len(chargingStations_df.score) * 100)
        pl.suptitle("Score of POI's (" + str(nrNA) + "% null)")
    
    # Get access
    chargingStations_df['access'] = chargingStations_df.access.map({1:'public',2:'restricted',3:'private'})
    
    # Get providers 
    # Get PlugShare providers from "stations" column (column type is dictionary)
    plugshare_providers = pd.read_csv(folder+"/Data Reference/PlugShare_Providers.csv",index_col="ID")
    chargingStations_df['plugshare_provider'] = [ [ y['network_id'] for y in ast.literal_eval(x) if y['network_id'] is not None] for x in chargingStations_df.stations ] # ast.literal_eval needed because stations is a dictionary but when stored in CSV becomes a string
    chargingStations_df['plugshare_provider'] = chargingStations_df['plugshare_provider'].apply(set).apply(list).map(lambda x: x[0] if (len(x)>0) else None)
    chargingStations_df['plugshare_provider'] = chargingStations_df.plugshare_provider.map(plugshare_providers.Providers)
    # Search local providers in "name", "description", "cost_description", "custom_ports" columns
    providers = get_providers_for_country(country)
    providers['provider'] = providers.Provider.str.lower().to_frame()
    chargingStations_df['local_provider'] = [", ".join(x) for i,x in chargingStations_df[['name','description','cost_description','custom_ports','plugshare_provider']].astype(str).iterrows()]
    chargingStations_df['local_provider'] = [next(iter(list(providers.ProviderUmbrella[[ x.lower().find(y) > -1 for y in providers.provider]] )),None) for x in chargingStations_df['local_provider']]
    chargingStations_df['provider'] = [ x.local_provider if pd.notna(x.local_provider) & (x.local_provider != "") else x.plugshare_provider for i, x in chargingStations_df.iterrows() ]
    
    # Count AC/DC connectors per station
    connectorTypes = pd.read_csv(folder+"/Data Reference/PlugShare_ConnectorTypes.csv",index_col="ID")
    connectors_df = pd.read_csv(folder+"/CSVs/PlugShare/"+country+"_Connectors_Raw.csv")
    connectors_df['connectorName'] = connectors_df['outlets.connector'].map(connectorTypes.Name)
    connectors_df['connectorType'] = connectors_df['outlets.connector'].map(connectorTypes.Type)
    chargingStations_df['NrACconnectors'] = chargingStations_df.id.map( connectors_df[connectors_df.connectorType=="AC"].groupby('id').connectorName.count())
    chargingStations_df['NrDCconnectors'] = chargingStations_df.id.map( connectors_df[connectors_df.connectorType=="DC"].groupby('id').connectorName.count())
    chargingStations_df['hasAC'] = (chargingStations_df.NrACconnectors > 0)*1
    chargingStations_df['hasDC'] = (chargingStations_df.NrDCconnectors > 0)*1
    
    # Get availability
    connectors_df['outlets.available'] = connectors_df['outlets.available'].map({0:"Unknown",1:"Available",2:"In Use",3:"Offline",4:"Under Repair"})
    chargingStations_df['availability'] = chargingStations_df.id.map(connectors_df[pd.notna(connectors_df['outlets.available'])].groupby('id')['outlets.available'].apply(lambda x: x.unique()))
    
    # Add source
    chargingStations_df['source'] = "PlugShare"
    
    # Standardize country
    chargingStations_df['country'] = country
    
    #=============================================================================================
    # Save to CSV
    #=============================================================================================
    chargingStations_df.to_csv(folder+"/CSVs/PlugShare/"+country+"_Processed.csv",encoding='utf_8_sig')
    connectors_df.to_csv(folder+"/CSVs/PlugShare/"+country+"_Connectors_Processed.csv",encoding='utf_8_sig')


#=============================================================================================
# Scrape data for countries
#=============================================================================================
countries = ['Romania','Slovakia','Hungary','Turkey','Thailand','Malaysia','Singapore','Indonesia','Australia','New Zealand','India','United Arab Emirates','Russia','South Korea','Japan']

countries = ["Brazil"]

for country in countries:
    scrapePlugShare(country,False)
#
#"""
## For Cara
#
#countries = ["United Arab Emirates","Israel","Chile","Colombia","Brazil","Argentina"]
#for country in countries:
#scrape_PlugShare(country, True)
#
#for country in countries:    
#folder = r"C:\Users\EEANNNG\WORK\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\Charging Stations Project"
#chargingStations_PlugShare_df = pd.read_csv(folder+"/CSVs/PlugShare/"+country+"_Processed.csv")
#print( country, chargingStations_PlugShare_df.shape[0], chargingStations_PlugShare_df[chargingStations_PlugShare_df.access!="public"].shape[0], chargingStations_PlugShare_df[chargingStations_PlugShare_df.access=="public"].shape[0], chargingStations_PlugShare_df[(chargingStations_PlugShare_df.access=="public")&(chargingStations_PlugShare_df.hasAC==True)].shape[0],chargingStations_PlugShare_df[(chargingStations_PlugShare_df.access=="public")&(chargingStations_PlugShare_df.hasDC==True)].shape[0] )
#"""    