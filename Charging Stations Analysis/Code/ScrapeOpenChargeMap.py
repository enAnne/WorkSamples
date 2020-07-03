# -*- coding: utf-8 -*-
"""
Created on Tue Feb 19 10:12:48 2019

@author: EEANNNG
"""

import pandas as pd
import numpy as np
import requests
import json
import matplotlib.pyplot as plt
import pandas.io.json as pd_json 
from Utils import hasNumbers, get_country_bounding_box, get_country_code, get_country, get_providers_for_country, get_country_bounding_box_stepsize, write_dfs_to_xlsx_sheets, read_xlsx_sheets_into_dfs, get_session

#=============================================================================================
# Modify this before run
#=============================================================================================
folder = r"C:\Users\EEANNNG\WORK\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\Charging Stations Project"
referenceExcel = folder+"/Data Reference/Open Charge Map Reference.xlsx"
    
def scrapeOpenChargeMap(country, fetchNewData):
    countryCode = get_country_code(country)    
    #=============================================================================================
    # Pull data from Open Charge Map API and store into CSV
    #=============================================================================================
    if fetchNewData==True:
        jsonFile = folder+'/JSONs/Open Charge Map/'+country+'.json'
        
        # Call API and store returned json data into json file
        chargingStations_json = []
        r = get_session().get('https://api.openchargemap.io/v3/poi/?output=json&countrycode='+ countryCode +'&maxresults=1000&compact=true&verbose=false')
        chargingStations_json = r.json()
        with open(jsonFile, 'w') as outfile:  
            json.dump(chargingStations_json, outfile)
                
        # Read data from JSON file
        with open(jsonFile,encoding="utf-8") as json_file:  
            chargingStations_json = json.load(json_file)
            chargingStations_df = pd_json.json_normalize(chargingStations_json)
            connectors_df = pd_json.json_normalize(chargingStations_json,record_path=['Connections'],meta =['ID'],record_prefix='Connector.') 
         
        # Open Charge Map Reference code
        r = get_session().get("https://api.openchargemap.io/v3/referencedata/")
        reference_json = r.json()
        connectionTypes_df = pd.DataFrame(reference_json['ConnectionTypes']).set_index('ID')
        chargerTypes_df = pd.DataFrame(reference_json['ChargerTypes']).set_index('ID')
        currentTypes_df = pd.DataFrame(reference_json['CurrentTypes']).set_index('ID')
        currentTypes_df['AC_DC'] = currentTypes_df.Title.apply(lambda x: x[:2])
        dataProviders_df = pd.DataFrame(reference_json['DataProviders']).set_index('ID').rename(columns={'Title':'Provider'})
        dataProviders_df = pd.concat( [dataProviders_df, dataProviders_df.DataProviderStatusType.apply(pd.Series)], axis = 1).drop(columns=['DataProviderStatusType'])
        operators_df = pd.DataFrame(reference_json['Operators']).set_index('ID')
        submissionStatus_df = pd.DataFrame(reference_json['SubmissionStatusTypes']).set_index('ID')
        statusTypes_df = pd.DataFrame(reference_json['StatusTypes']).set_index('ID')
        usageTypes_df = pd.DataFrame(reference_json['UsageTypes']).set_index('ID')
        usageTypes_df['access'] = [ 'private' if (x.find('Private')>-1) else 'public' for x in usageTypes_df.Title]
        countries_df = pd.DataFrame(reference_json['Countries']).set_index('ID')
        dfs = [connectionTypes_df,chargerTypes_df,currentTypes_df,dataProviders_df,operators_df,submissionStatus_df,statusTypes_df,usageTypes_df,countries_df]
        names = ["ConnectionTypes","ChargerTypes","CurrentTypes","DataProviders","Operators","SubmissionStatusTypes","StatusTypes","UsageTypes","Countries"]
        write_dfs_to_xlsx_sheets(dfs,names,referenceExcel)
        
        # Save to CSVs
        chargingStations_df = chargingStations_df.drop_duplicates('ID')
        chargingStations_df = chargingStations_df.drop_duplicates(['AddressInfo.Title','AddressInfo.Latitude','AddressInfo.Longitude'])
        chargingStations_df.to_csv(folder+"/CSVs/Open Charge Map/"+country+"_Raw.csv",encoding='utf_8_sig')
        connectors_df.to_csv(folder+"/CSVs/Open Charge Map/"+country+"_Connectors_Raw.csv",encoding='utf_8_sig')
    
    #=============================================================================================
    # Enrich data
    #=============================================================================================
    # Read data from CSV    
    chargingStations_df = pd.read_csv(folder+"/CSVs/Open Charge Map/"+country+"_Raw.csv",index_col="ID")
    
    names = ["ConnectionTypes","ChargerTypes","CurrentTypes","DataProviders","Operators","SubmissionStatusTypes","StatusTypes","UsageTypes","Countries"]
    [connectionTypes_df,chargerTypes_df,currentTypes_df,dataProviders_df,operators_df,submissionStatus_df,statusTypes_df,usageTypes_df,countries_df] = read_xlsx_sheets_into_dfs(names, referenceExcel)
    
    # Get providers 
    # Get Open Charge Map providers from "Operator" column (column type is dictionary)
    chargingStations_df['Operator'] = chargingStations_df.OperatorID.map(operators_df.Title)
    chargingStations_df['OperatorWebsite'] = chargingStations_df.OperatorID.map(operators_df.WebsiteURL)
    chargingStations_df['DataProvider'] = chargingStations_df.DataProviderID.map(dataProviders_df.Provider)
    # Search local providers in "GeneralComments", "AccessComments", "MediaItems" columns
    providers = get_providers_for_country(country)
    providers['provider'] = providers.Provider.str.lower().to_frame()
    chargingStations_df['MediaItems'] = chargingStations_df['MediaItems'] if 'MediaItems' in chargingStations_df.columns else ""
    chargingStations_df['GeneralComments'] = chargingStations_df['GeneralComments'] if 'GeneralComments' in chargingStations_df.columns else ""
    chargingStations_df['AddressInfo.AccessComments'] = chargingStations_df['AddressInfo.AccessComments'] if 'AddressInfo.AccessComments' in chargingStations_df.columns else ""
    chargingStations_df['local_provider'] = [", ".join(x) for i,x in chargingStations_df[['AddressInfo.Title','GeneralComments','AddressInfo.AccessComments','MediaItems','AddressInfo.Title','Operator']].astype(str).iterrows()]
    chargingStations_df['local_provider'] = [next(iter(list(providers.ProviderUmbrella[[ x.lower().find(y) > -1 for y in providers.provider]] )),None) for x in chargingStations_df['local_provider']]
    chargingStations_df['provider'] = [ x.local_provider if pd.notna(x.local_provider) & (x.local_provider != "") else x.Operator for i, x in chargingStations_df.iterrows() ]
    
    # Get access
    chargingStations_df['Access'] = chargingStations_df.UsageTypeID.map(usageTypes_df.access)
    
    # Get availability
    chargingStations_df['DataImportMethod'] = chargingStations_df.DataProviderID.map(dataProviders_df.Title)
    chargingStations_df['ChargingStatus'] = chargingStations_df.StatusTypeID.map(statusTypes_df.Title)
    
    # Count AC/DC connectors per station
    connectors_df = pd.read_csv(folder+"/CSVs/Open Charge Map/"+country+"_Connectors_Raw.csv",index_col="ID")
    connectors_df['ConnectionType'] = connectors_df['Connector.ConnectionTypeID'].map(connectionTypes_df.Title)
    connectors_df['Unusable'] = connectors_df['Connector.ConnectionTypeID'].map(connectionTypes_df.IsDiscontinued) + connectors_df['Connector.ConnectionTypeID'].map(connectionTypes_df.IsObsolete)
    connectors_df = connectors_df[pd.isna(connectors_df.Unusable) | (connectors_df.Unusable==0)]
    connectors_df['FastCharging'] = connectors_df['Connector.LevelID'].map(chargerTypes_df.IsFastChargeCapable)
    connectors_df['ChargerLevel'] = connectors_df['Connector.LevelID'].map(chargerTypes_df.Title)
    connectors_df['CurrentType'] = connectors_df['Connector.CurrentTypeID'].map(currentTypes_df.Title)
    connectors_df['AC_DC'] = connectors_df['Connector.CurrentTypeID'].map(currentTypes_df.AC_DC)
    connectors_df['AC_DC'] = connectors_df['Connector.CurrentTypeID'].map(currentTypes_df.AC_DC)
    connectors_df['Status'] = connectors_df['Connector.StatusTypeID'].map(statusTypes_df.Title)
    chargingStations_df['NrACconnectors'] = chargingStations_df.index.map(connectors_df[connectors_df.AC_DC=="AC"].groupby(connectors_df[connectors_df.AC_DC=="AC"].index)['Connector.Quantity'].sum())
    chargingStations_df['NrDCconnectors'] =  chargingStations_df.index.map(connectors_df[connectors_df.AC_DC=="DC"].groupby(connectors_df[connectors_df.AC_DC=="DC"].index)['Connector.Quantity'].sum())
    chargingStations_df['hasAC'] = (chargingStations_df.NrACconnectors > 0)*1
    chargingStations_df['hasDC'] = (chargingStations_df.NrDCconnectors > 0)*1
    
    # Process Address (StreetNumber is within AddressLine1)
    chargingStations_df['streetNumber_strings'] = chargingStations_df['AddressInfo.AddressLine1'].str.split()
    chargingStations_df['streetNumber_hasNumber'] = chargingStations_df.streetNumber_strings.apply(lambda x: [i for i,y in enumerate(x) if hasNumbers(y) ] if x==x else [])
    chargingStations_df['streetNumber'] = [ x[0][x[1][-1]].replace(",","") if (len(x[1])>0) else "" for i,x in chargingStations_df[['streetNumber_strings','streetNumber_hasNumber']].iterrows() ]
    chargingStations_df['street'] = [ x[0].replace(x[1],"") if (len(x[1])>0) else "" for i,x in chargingStations_df[['AddressInfo.AddressLine1','streetNumber']].iterrows() ]
    chargingStations_df['CountryCode'] = chargingStations_df['AddressInfo.CountryID'].map(countries_df.ISOCode)
    chargingStations_df['Country'] = chargingStations_df['CountryCode'].apply(lambda x: get_country(x))
    chargingStations_df['AddressInfo.StateOrProvince'] = chargingStations_df['AddressInfo.StateOrProvince'] if 'AddressInfo.StateOrProvince' in chargingStations_df.columns else ""
    chargingStations_df['Address'] = [", ".join(x) for i,x in chargingStations_df[['streetNumber','street','AddressInfo.AddressLine2','AddressInfo.Town','AddressInfo.StateOrProvince','AddressInfo.Postcode','Country']].astype(str).iterrows()]
    #chargingStations_df['Postcode'] = pd.to_numeric(chargingStations_df['Postcode'], downcast = "integer", errors = "coerce" )
    
    # Add source
    chargingStations_df['source'] = "Open Charge Map"
    
    # Standardize country
    chargingStations_df = chargingStations_df[chargingStations_df['Country']==country]
    
    #=============================================================================================
    # Save to CSV
    #=============================================================================================
    chargingStations_df.to_csv(folder+"/CSVs/Open Charge Map/"+country+"_Processed.csv",encoding='utf_8_sig')
    connectors_df.to_csv(folder+"/CSVs/Open Charge Map/"+country+"_Connectors_Processed.csv",encoding='utf_8_sig')


#=============================================================================================
# Scrape data for countries ('South Korea','Thailand','Indonesia' no POIs)
#=============================================================================================
countries = ['Australia','Romania','Slovakia','Hungary','Turkey','Malaysia','Singapore','New Zealand','India','United Arab Emirates','Russia','Japan']

#for country in countries:
countries = ["Brazil"]

for country in countries:
    scrapeOpenChargeMap(country,False)
