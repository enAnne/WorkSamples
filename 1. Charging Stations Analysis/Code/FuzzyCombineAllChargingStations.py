# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 07:02:56 2019

@author: EEANNNG
"""
import os
import pandas as pd
import numpy as np
from fuzzywuzzy import process, fuzz
from scipy.optimize import linear_sum_assignment
from math import sin, cos, sqrt, atan2, radians
from collections import Counter
import itertools
from Utils import search_exact_string_in_DF, get_providers_for_country
import ast

"""
Process
1. Minimize geo_distance x1000                          -> Cut off at ? for each country
2. Minimize geo_distance x100 - string_similarity x1    -> Cut off at ? for each country
"""

def get_dataframe(df,df_columns,desired_columns):
    # Accepts a dataframe and the names of the desired columns and rename them to the ones in [coordinates,string_ids,non_ids]
    df['blank'] = None
    df_columns = ['blank' if x == "" else x for x in df_columns]
    df = df[df_columns]
    df.columns=desired_columns
    return df
    
def haversine(lat1,lon1,lat2,lon2):
    # Calculate the distance in KM between two geo-coordinates
    distance = 1000
    if pd.notna(lat1) and pd.notna(lat2) and pd.notna(lon1) and pd.notna(lon2): 
        R = 6373.0 # earth radius in km
        lat1 = radians(lat1)
        lon1 = radians(lon1)
        lat2 = radians(lat2)
        lon2 = radians(lon2)
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c
    return distance

def geo_distance_matrix(coordinates1, coordinates2, isFirst=True):
    # Create a 2D matrix of haversine distances between 2 series of geo-coordinate points
    len1 = len(coordinates1)
    len2 = len(coordinates2)
    matrix = np.empty([len1,len2])
    for i,r1 in coordinates1.iterrows():
        for j,r2 in coordinates2.iterrows():
            # If it is not the first run, the left table will contain a pool of values, and right table is added to the pool 
            if( isFirst==False ):
                distance = []
                for k in range(len(r1[0])):
                    distance = distance + [haversine(r1[0][k],r1[1][k],r2[0],r2[1])]
                matrix[i,j] = min(distance) if len(distance)>0 else 1000
            else:
                matrix[i,j] = haversine(r1[0],r1[1],r2[0],r2[1])
    return matrix

def string_similarity_matrix(series1, series2, isFirst=True):
    # Create a 2D matrix of lavenshtein distances between 2 series of strings
    len1 = len(series1)
    len2 = len(series2)
    matrix = np.empty([len1,len2])
    for i,s1 in enumerate(series1):
        for j,s2 in enumerate(series2):
            # Combined is where left table contains a pool of values, and right table is added to the pool 
            if( isFirst==False ):
                similarity = []
                for k,s1_e in enumerate(s1):
                    similarity = similarity + [fuzz.token_set_ratio(s1_e, s2)]
                matrix[i,j] = max(similarity+[0])
            else:
                matrix[i,j] = fuzz.token_set_ratio(s1, s2)
    return matrix

def minimize(score):
    # Perform assignment to minimize total cost
    # Add padding of high cost to create a square matrix, if nrRows more than nrCols (left table longer than right table)
    nrRows = score.shape[0]
    nrCols = score.shape[1]
    size_diff = nrRows - nrCols
    if(size_diff>0):
        score = np.pad(score, ((0,0), (0,size_diff)), mode='constant', constant_values=1e10)
    # Solve assignment problem (linear_sum_assignment assigns columns to rows, throws error if nrRows more than nrCols)
    row_ind, assignment = linear_sum_assignment(score)
    scores = [score[i,x] for i,x in enumerate(assignment)]
    total = score[row_ind, assignment].sum()
    # Tabulate assignments to score
    assignment = pd.concat( [pd.DataFrame(assignment), pd.DataFrame(scores)], axis=1)
    assignment.columns = ['assignment','score']
    # Handle assignments that are assigned to padding columns (means they are not assigned)
    # (re-assign them to the last row of the right table, which is an appended null row)
    assignment.loc[assignment.assignment>=nrCols,'assignment'] = nrCols
    return assignment, total
    
def geo_string_match(df1,df2,coordinates,string_ids,non_ids,distance_threshold,geo_weight,string_weight,isFirst,file='Merge.csv'):
    # Create matrix for geo-coordinate distance and string similarity, and perform assignment to minimize total cost
    df1 = df1.reset_index().drop('index',axis=1)
    df2 = df2.reset_index().drop('index',axis=1)
    
    geo_distance = np.ones([len(df1),len(df2)]) * (distance_threshold + 1)
    # Calculate matrix of distances between every 2 geo-coordinate
    if geo_weight > 0:
        geo_distance = geo_distance_matrix(df1[coordinates],df2[coordinates],isFirst)
        geo_distance[np.isnan(geo_distance)] = distance_threshold + 1
    
    # Calculate matrices of similarity between every 2 string-attribute, and sum them into 1 matrix
    string_similarity_total = np.zeros([len(df1),len(df2)])
    if string_weight > 0:
        for s in string_ids:
            string_similarity = string_similarity_matrix(df1[s],df2[s],isFirst)
            string_similarity_total = string_similarity + string_similarity_total
    
    # Solve assignment problem to minimize the total cost of (distance - similarity)
    assignment, final_score = minimize( geo_weight * geo_distance - string_weight * string_similarity_total )
    
    # Join the assigned rows of right table and left table into 1 table 
    # (in case right table is longer than left table, append a dummy row to the right table to be assigned to unassigned left table rows)
    df2_match = df2.append(pd.Series(), ignore_index=True).iloc[assignment.loc[:,'assignment'],:] 
    df2_match = df2_match.reset_index().drop('index',axis=1)
    df1.columns = [s + '1' if (s!='index1') else s for s in df1.columns]
    df2_match.columns = [s + '2' if (s!='index2') else s for s in df2_match.columns]
    df_matched = pd.concat([assignment.loc[:,'score'],df1,df2_match],axis=1)
    df_matched = df_matched.sort_values('score')
    
    # Rearrange columns in table to create alternating column headers (only for columns of interest): columns1, columns2
    cols1 = ['index1'] + [s + '1' for s in string_ids] + [s + '1' for s in coordinates] + [s + '1' for s in non_ids]
    cols2 = ['index2'] + [s + '2' for s in string_ids] + [s + '2' for s in coordinates] + [s + '2' for s in non_ids]
    cols = [None]*(len(cols1)+len(cols2))
    cols[::2] = cols1
    cols[1::2] = cols2
    df_matched = df_matched[['score']+cols]
    df_matched.to_csv(file,encoding="utf_8_sig")
    
    return df_matched

def combine_datasets(df_match, desired_columns, isFirst=True):
    # Combine columns1 and columns2 values into a list and store in columns1
    if( isFirst==True ) :
        # First time, both columns1 and columns2 are not lists
        for col in desired_columns:
            #df_match[col+'1'] = [ list(set(x[pd.notnull(x)])) for i,x in df_match[[col+'1',col+'2']].iterrows() ] # Removes nulls and repeats
            df_match[col+'1'] = [ list(x) for i,x in df_match[[col+'1',col+'2']].iterrows() ] # Doesn't remove nulls and repeats
    else:
        # Subsequent times, columns1 are lists and columns2 are not
        for col in desired_columns:
            #df_match[col+'1'] = [ list(filter(pd.notna, set(x[col+'1'] + [x[col+'2']]))) for i,x in df_match[[col+'1',col+'2']].iterrows() ] # Removes nulls and repeats 
            df_match[col+'1'] = [ list((x[col+'1'] + [x[col+'2']])) for i,x in df_match[[col+'1',col+'2']].iterrows() ] # Doesn't remove nulls and repeats  
        
    # Retain only columns1, then remove the "1".
    df_match = df_match[[ x+'1' for x in desired_columns ]]
    df_match.columns = desired_columns
    
    return df_match

def merge_datasets(df1,df2,desired_columns,coordinates,string_ids,non_ids,isFirst,merged_sources):
    file = folder + "/Fuzzy Merged CSVs/" + country + "_" + merged_sources
    
    distance_threshold,geo_weight1,string_weight1=get_threshold_weights(df1, df2, desired_columns, string_ids, coordinates, True)
    string_threshold,geo_weight2,string_weight2=get_threshold_weights(df1, df2, desired_columns, string_ids, coordinates, False)
    print(merged_sources)
    print("distance_threshold:",distance_threshold,"string_threshold",string_threshold)
    print("geo_weight1",geo_weight1,"string_weight1",string_weight1)
    print("geo_weight2",geo_weight2,"string_weight2",string_weight2)
    
    # Reset index to be continuous
    df1 = df1.reset_index().reset_index().rename(columns={'level_0':'index1'}).drop('index',axis=1)
    df2 = df2.reset_index().reset_index().rename(columns={'level_0':'index2'}).drop('index',axis=1)
    
    # 1st round, match only on geo-coordinates
    df_geomatch = geo_string_match(df1,df2,coordinates,string_ids,non_ids,distance_threshold,geo_weight1,string_weight1,isFirst,file+'_Merged_GeoMatch.csv')
    # Accept matches whose distance is less than ???km
    df_geomatch = df_geomatch[df_geomatch.score <= distance_threshold]   # DEFINE CUT-OFF DISTANCE!!!!!
    # Get unmatched data to be further matched using string comparison
    df1 = df1[~df1['index1'].isin(df_geomatch.index1)] 
    df2 = df2[~df2['index2'].isin(df_geomatch.index2)] 
    
    # 2nd round matching on unmatched data, match on geo-coordinates distance and similarity on string_identifiers
    df_stringmatch = geo_string_match(df1,df2,coordinates,string_ids,non_ids,distance_threshold,geo_weight2,string_weight2,isFirst,file+'_Merged_StringMatch.csv')
    # Accept matches whose score is less than ???
    df_stringmatch = df_stringmatch[df_stringmatch.score <= string_threshold]   # DEFINE CUT-OFF SCORE!!!!!
    # Get unmatched data
    df1 = df1[~df1['index1'].isin(df_stringmatch.index1)] 
    df2 = df2[~df2['index2'].isin(df_stringmatch.index2)] 
    
    # Combine matches from 1st & 2nd round
    df_match = pd.concat([df_geomatch,df_stringmatch])
    
    # Combine data in columns1 and columns2 to form a list of possible values
    df_match = combine_datasets(df_match,desired_columns,isFirst)
    # Append unmatched data to matched data, in the form of lists (single element)
    if( isFirst==True ):
        df1 = df1.apply(lambda x: x.apply(lambda y: [y] if pd.notnull(y) else []))
    df2 = df2.apply(lambda x: x.apply(lambda y: [y] if pd.notnull(y) else []))
    df_match = pd.concat([df_match,df1,df2],sort=False).drop(['index1','index2'],axis=1)
        
    return df_match

def enrich_datasets(df_match, non_ids, country):
    df_enrich = df_match.copy()
    
    df_enrich['source'] = [", ".join(x) for x in df_enrich['source']]
    
    # Special columns - AC and DC count, take the bigger value
    df_enrich['hasAC'] = [max(list(filter(None,x))) if len(list(filter(None,x)))>0 else 0 for x in df_enrich['hasAC']]
    df_enrich['hasDC'] = [max(list(filter(None,x))) if len(list(filter(None,x)))>0 else 0 for x in df_enrich['hasDC']]
    
    # Special columns - Latitude and Longitude, take the average
    df_enrich['latitude'] = [ np.mean(list(filter(None,x))) for x in df_enrich['latitude']]
    df_enrich['longitude'] = [ np.mean(list(filter(None,x))) for x in df_enrich['longitude']]
       
    # Special column - Listed General Providers should be given priority
    providers = get_providers_for_country(country)
    providers['provider'] = providers.Provider.str.lower().to_frame()
    df_enrich['provider'] = [ list(filter(lambda y:pd.notna(y) and (y!=""),x)) for x in df_enrich['provider']]
    df_enrich['local_provider'] = [[next(iter(list(providers.ProviderUmbrella[[ x.lower().find(y) > -1 for y in providers.provider]] )),None) if pd.notnull(x) else "" for x in y ] for y in df_enrich['provider']]
    df_enrich['provider_seq'] = [[providers[providers.ProviderUmbrella==p].first_valid_index() for p in x] for x in df_enrich['local_provider']]
    df_enrich['provider_seq'] = [[9999 if v is None else v for v in x] for x in df_enrich['provider_seq']]
    df_enrich['provider'] = [ [i[1] for i in sorted(zip(x[1], x[0]))] for j,x in df_enrich[['local_provider','provider_seq']].iterrows()]
    df_enrich = df_enrich.drop(columns=['provider_seq','local_provider'],axis=1)
    
    # Get the majority vote value for the non_ids
    for col in non_ids + ['postalCode','name','address']:
        if( ( col in ['hasAC','hasDC','source'] ) == False ):
            df_enrich[col] = [ Counter(list(filter(lambda y:pd.notna(y) and (y!=""),x))).most_common(1) for x in df_enrich[col] ]
            df_enrich[col][df_enrich[col].str.len()>0] = [ x[0][0] for x in df_enrich[col][df_enrich[col].str.len()>0] ]
            
    df_enrich[['provider','access']] = df_enrich[['provider','access']].mask(df_enrich[['provider','access']].applymap(str).eq('[]')).fillna("Unknown")
    
    return df_enrich

# To read in a CSV whose columns contain lists
def read_csv_columns_as_lists(file):    
    df = pd.read_csv(file,encoding="utf_8_sig",nrows=1)
    d = {}
    for i in range(0,len(df.columns)):
        d[i]=lambda x: ast.literal_eval(x.replace("nan, ","").replace(",nan ","").replace("nan",""))
    df = pd.read_csv(file,encoding="utf_8_sig",converters=d) 
    return df

#=============================================================================================
# Set the thresholds and weights
#=============================================================================================
def get_threshold_weights(df1, df2, desired_columns, string_ids, coordinates, isDistanceOnly):    
    # Check for the nullness of the columns of comparison
    # Geomatching is using only coordinates, string matching uses 'name','streetNumber','street','postalCode','city','address'
    hasCoordinates = all([not all(pd.isna(df1.iloc[:,y])) and not all(pd.isna(df2.iloc[:,y])) for y in [desired_columns.index(x) for x in coordinates]])
    nrStringIDs = sum([not all(pd.isna(df1.iloc[:,y])) and not all(pd.isna(df2.iloc[:,y])) for y in [desired_columns.index(x) for x in string_ids]])
    distance_threshold = 150 if hasCoordinates else 0
    string_threshold = -nrStringIDs * 65 + hasCoordinates * 30
    threshold = distance_threshold if isDistanceOnly else string_threshold
    # If there are no coordinates, the geomatching weight is set to 0 during stringmatching so as not to affect the string matching score
    geo_weight = ( 1000 if isDistanceOnly else 100 ) if hasCoordinates else ( 1 if isDistanceOnly else 0 )
    string_weight = 0 if isDistanceOnly else 1
    return threshold, geo_weight, string_weight

#=============================================================================================
# Define columns
#=============================================================================================    
coordinates=['latitude','longitude']
string_ids=['name','streetNumber','street','postalCode','city','address']
non_ids=['country','provider','hasAC','hasDC','access','source']
desired_columns = string_ids+coordinates+non_ids

#=============================================================================================
# Load data
#=============================================================================================
folder = r"C:\Users\EEANNNG\WORK\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\Charging Stations Project"

countries = ['Singapore','Indonesia','New Zealand','India','United Arab Emirates','Russia','Australia','Japan','South Korea']

countries = ["South Korea"]

for country in countries:
    hasOpenStreetMap = country+"_Processed.csv" in os.listdir(folder+"/CSVs/OpenStreetMap")
    hasOpenChargeMap = country+"_Processed.csv" in os.listdir(folder+"/CSVs/Open Charge Map")
    hasPlugShare = country+"_Processed.csv" in os.listdir(folder+"/CSVs/PlugShare")
    hasHERE = country+"_Processed.csv" in os.listdir(folder+"/CSVs/HERE")
    hasNewMotion = country+"_Processed.csv" in os.listdir(folder+"/CSVs/NewMotion")
    hasPlugSurfing = country+"_Processed.csv" in os.listdir(folder+"/CSVs/PlugSurfing")
    hasEAnywhere = country+"_Processed.csv" in os.listdir(folder+"/CSVs/EAnywhere")
    hasEVstationMY = country+"_Processed.csv" in os.listdir(folder+"/CSVs/EVstationMY")
    hasNZgov = country+"_Processed.csv" in os.listdir(folder+"/CSVs/NZ gov")
    hasNaver = country+"_Processed.csv" in os.listdir(folder+"/CSVs/Naver")
    
    chargingStations_HERE_df = pd.DataFrame()
    chargingStations_PlugShare_df = pd.DataFrame()
    chargingStations_OpenChargeMap_df = pd.DataFrame()
    chargingStations_OpenStreetMap_df = pd.DataFrame()
    chargingStations_PlugSurfing_df = pd.DataFrame()
    chargingStations_NewMotion_df = pd.DataFrame()
    chargingStations_EAnywhere_df = pd.DataFrame()
    chargingStations_EVstationMY_df = pd.DataFrame()
    chargingStations_NZgov_df = pd.DataFrame()
    chargingStations_Naver_df = pd.DataFrame()
            
    # Get desired columns in data (in the right order) and standardize column naming
    if hasOpenStreetMap:
        chargingStations_OpenStreetMap_df = pd.read_csv(folder+"/CSVs/OpenStreetMap/"+country+"_Processed.csv")
        chargingStations_OpenStreetMap_columns = ['name_operator','','','','','','latitude','longitude','addr:country','provider','hasAC','hasDC','','source']#['name_operator','addr:housenumber','addr:street','','addr:city','','latitude','longitude','addr:country','provider','hasAC','hasDC','access','source']
        chargingStations_OpenStreetMap_df = get_dataframe(chargingStations_OpenStreetMap_df,chargingStations_OpenStreetMap_columns,desired_columns)
        
    if hasOpenChargeMap:
        chargingStations_OpenChargeMap_df = pd.read_csv(folder+"/CSVs/Open Charge Map/"+country+"_Processed.csv")
        chargingStations_OpenChargeMap_columns = ['AddressInfo.Title','streetNumber','street','AddressInfo.Postcode','AddressInfo.Town','Address','AddressInfo.Latitude','AddressInfo.Longitude','Country','provider','hasAC','hasDC','Access','source']
        chargingStations_OpenChargeMap_df = get_dataframe(chargingStations_OpenChargeMap_df,chargingStations_OpenChargeMap_columns,desired_columns)
        
    if hasPlugShare:
        chargingStations_PlugShare_df = pd.read_csv(folder+"/CSVs/PlugShare/"+country+"_Processed.csv")
        chargingStations_PlugShare_columns = ['name','streetNumber','street','postalCode','city','address','latitude','longitude','country','provider','hasAC','hasDC','access','source']
        chargingStations_PlugShare_df = get_dataframe(chargingStations_PlugShare_df,chargingStations_PlugShare_columns,desired_columns)
    
    if hasHERE:
        chargingStations_HERE_df = pd.read_csv(folder+"/CSVs/HERE/"+country+"_Processed.csv")
        chargingStations_HERE_columns = ['name','address.streetNumber','address.street','address.postalCode','address.city','address','position.latitude','position.longitude','address.country','provider','hasAC','hasDC','access','source']
        chargingStations_HERE_df = get_dataframe(chargingStations_HERE_df,chargingStations_HERE_columns,desired_columns)
    
    if hasNewMotion:
        chargingStations_NewMotion_df = pd.read_csv(folder+"/CSVs/NewMotion/"+country+"_Processed.csv")
        chargingStations_NewMotion_columns = ['name','streetNumber','street','address.postalCode','address.city','address','coordinates.latitude','coordinates.longitude','address.country','provider','hasAC','hasDC','access','source']
        chargingStations_NewMotion_df = get_dataframe(chargingStations_NewMotion_df,chargingStations_NewMotion_columns,desired_columns)
    
    if hasPlugSurfing:
        chargingStations_PlugSurfing_df = pd.read_csv(folder+"/CSVs/PlugSurfing/"+country+"_Processed.csv")
        chargingStations_PlugSurfing_columns = ['name','address.streetNumber','address.street','address.zip','address.city','address','latitude','longitude','address.country','provider','hasAC','hasDC','access','source']
        chargingStations_PlugSurfing_df = get_dataframe(chargingStations_PlugSurfing_df,chargingStations_PlugSurfing_columns,desired_columns)
    
    if hasEAnywhere:
        chargingStations_EAnywhere_df = pd.read_csv(folder+"/CSVs/EAnywhere/"+country+"_Processed.csv")
        chargingStations_EAnywhere_columns = ['name','streetNumber','street','postalCode','city','address','latitude','longitude','country','provider','hasAC','hasDC','access','source']
        chargingStations_EAnywhere_df = get_dataframe(chargingStations_EAnywhere_df,chargingStations_EAnywhere_columns,desired_columns)
        
    if hasEVstationMY:
        chargingStations_EVstationMY_df = pd.read_csv(folder+"/CSVs/EVstationMY/"+country+"_Processed.csv")
        chargingStations_EVstationMY_columns = ['Name','','','','','Address','','','country','','hasAC','hasDC','','source']
        chargingStations_EVstationMY_df = get_dataframe(chargingStations_EVstationMY_df,chargingStations_EVstationMY_columns,desired_columns)
        
    if hasNZgov:
        chargingStations_NZgov_df = pd.read_csv(folder+"/CSVs/NZ gov/"+country+"_Processed.csv")
        chargingStations_NZgov_columns = ['name','street_number','street','zip','city','address','latitude','longitude','country','provider','hasAC','hasDC','','source']
        chargingStations_NZgov_df = get_dataframe(chargingStations_NZgov_df,chargingStations_NZgov_columns,desired_columns)
        
    if hasNaver:
        chargingStations_Naver_df = pd.read_csv(folder+"/CSVs/Naver/"+country+"_Processed.csv")
        chargingStations_Naver_columns = ['name','BUILDING_NUMBER','DONGMYUN','POSTAL_CODE','SIGUGUN','jibunAddress','y','x','country','','','','','source']
        chargingStations_Naver_df = get_dataframe(chargingStations_Naver_df,chargingStations_Naver_columns,desired_columns)
    
    #=============================================================================================
    # Merge datasets and select best value
    #=============================================================================================
    # Create merged pool of values from all data sources
    folder = r"C:\Users\EEANNNG\WORK\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\Charging Stations Project"
    dataSourcesAll = ["PlugShare", "HERE", "Open Charge Map", "OpenStreetMap", "PlugSurfing", "NewMotion", "EAnywhere", "EVstationMY","NZ gov","Naver"]
    dfs = [chargingStations_PlugShare_df, chargingStations_HERE_df, chargingStations_OpenChargeMap_df, chargingStations_OpenStreetMap_df, chargingStations_PlugSurfing_df, chargingStations_NewMotion_df, chargingStations_EAnywhere_df, chargingStations_EVstationMY_df, chargingStations_NZgov_df, chargingStations_Naver_df]
    # Sort the data sources based on size, biggest one to be merged last (speeds up the matching process)
    dfs_size = [len(df) for df in dfs]
    dfs_sortIndex = np.argsort(dfs_size)
    dfs_size = [dfs_size[i] for i in dfs_sortIndex]
    dfs = [dfs[i] for i,size in zip(dfs_sortIndex,dfs_size) if size > 0]
    dataSources = [dataSourcesAll[i] for i,size in zip(dfs_sortIndex,dfs_size) if size > 0]
    
    df1 = dfs[0]
    merged_sources = dataSources[0]
    isFirst=True
    i=0
    for source, df in zip(dataSources[1:],dfs[1:]):
        merged_sources = merged_sources + "_" + source
        df2 = df
        df_match = merge_datasets(df1,df2,desired_columns,coordinates,string_ids,non_ids,isFirst,merged_sources) 
        df_match.to_csv(folder+"/Fuzzy Merged CSVs/"+country+"_"+merged_sources+"_Merged_All.csv",encoding="utf_8_sig")
        isFirst = False
        df1 = df_match
        i = i+2
            
    # Finalize the selection (choose the majority vote value as final)
    df_enrich = enrich_datasets(df_match,non_ids,country)
    df_enrich.to_csv(folder+"/Fuzzy Merged CSVs/"+country+'_Enriched_All.csv',encoding="utf_8_sig")

#=============================================================================================
# Compile all market analysis data into "Market Analysis All.csv"
#=============================================================================================
folder = r"C:\Users\EEANNNG\WORK\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\Charging Stations Project\PowerBI\Market Analysis"

files = []  
for file in os.listdir(folder):
    if file.endswith("_market analysis.xlsx") & (file.startswith("~$")==False):
        files = files + [os.path.join(folder, file)]
       
market_analysis_df = pd.DataFrame()        
for f in files:        
    xls = pd.ExcelFile(f)      
    df = xls.parse("Partner analysis ")
    
    c = f.split(" ")[-2].split("_")[0]
    allCols = list(df.columns)
    stakeholder_col = allCols.index(search_exact_string_in_DF("Stakeholder",df).index[0])
    stakeholder_row = list(df.iloc[:,stakeholder_col]).index("Stakeholder")
    cutoff_col = list(pd.isna(df.iloc[stakeholder_row,stakeholder_col:])).index(True)
    provider = df.iloc[stakeholder_row,stakeholder_col:][1:cutoff_col].dropna()
    nrAC = df.iloc[stakeholder_row+4,stakeholder_col:][1:cutoff_col].dropna()
    nrDC = df.iloc[stakeholder_row+7,stakeholder_col:][1:cutoff_col].dropna()
    totalPOI = nrAC + nrDC
    market_analysis_df = pd.concat([ market_analysis_df,pd.DataFrame({'country':c,'provider':provider,'nrAC':nrAC,'nrDC':nrDC,'totalPOI':totalPOI})], ignore_index=True)
    market_analysis_df = market_analysis_df.dropna(subset=["nrAC","nrDC","totalPOI"])
    market_analysis_df = market_analysis_df.replace('\n','', regex=True)
    
market_analysis_df.to_csv(folder+"/Market Analysis All.csv",encoding="utf_8_sig")

#=============================================================================================
# Compile all enriched data into "Enriched_All.csv"
#=============================================================================================
folder = r"C:\Users\EEANNNG\WORK\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\Charging Stations Project\Fuzzy Merged CSVs"

re_enrich = True
# Retrieve all Country_Merged_All.csv and re-enrich data
if re_enrich == True:
    files = pd.DataFrame(columns=['Country','File','Length'])  
    for file in os.listdir(folder):
        if file.endswith("Merged_All.csv") & (file.startswith("~$")==False):
            filePath = os.path.join(folder, file)
            country = file.split("\\")[-1].split("_")[0]
            row = pd.Series({'Country':country,'File':filePath,'Length':len(filePath)})
            files = files.append(row,ignore_index=True)
    files = files.sort_values('Length').drop_duplicates(subset=['Country'],keep='last')  
    
    for i,row in files.iterrows(): 
        df_match = read_csv_columns_as_lists(row.File)
        df_enrich = enrich_datasets(df_match,non_ids,row.Country)
        df_enrich.to_csv(folder+'/'+row.Country+'_Enriched_All.csv',encoding="utf_8_sig")
    
# Get all Country_Enriched_All.csv files and compile into Enriched_All.csv
enriched_all_file = r"C:\Users\EEANNNG\WORK\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\Charging Stations Project\PowerBI\Enriched_All.csv"
enriched_all_df = pd.read_csv(enriched_all_file)

files = []  
for file in os.listdir(folder):
    if file.endswith("Enriched_All.csv") & (file.startswith("~$")==False):
        files = files + [os.path.join(folder, file)]

# Go through all Country_DataSources_Enriched_All.csv and combine data into Enriched_All.csv    
new_enriched_all_df = pd.DataFrame()        
for f in files:        
    df = pd.read_csv(f) 
    country = f.split("\\")[-1].split("_")[0]
    new_enriched_all_df = pd.concat( [df, new_enriched_all_df] )
    enriched_all_df = enriched_all_df[enriched_all_df.country != country] # Remove data for that country
    
new_enriched_all_df.rename(columns={"hasAC":"NrACconnectors","hasDC":"NrDCconnectors","provider":"providers"},inplace=True)    
enriched_all_df = pd.concat([ enriched_all_df, new_enriched_all_df ])
enriched_all_df = enriched_all_df.drop(list(enriched_all_df.filter(regex='Unnamed')),axis=1)
enriched_all_df.reset_index(inplace=True)
enriched_all_df = enriched_all_df.drop(["index"],axis=1)
enriched_all_df = enriched_all_df.replace('\n','', regex=True)
enriched_all_df = enriched_all_df.replace('\n','', regex=True)
enriched_all_df.to_csv(enriched_all_file,encoding="utf_8_sig")

#=============================================================================================
# Create 'Sources', 'Source', 'SourcesToSource' relationship for tables in PowerBI
#=============================================================================================
folder = r"C:\Users\EEANNNG\WORK\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\Charging Stations Project\PowerBI"
os.chdir(folder)
pd.DataFrame({'Source':dataSourcesAll}).to_csv("Source.csv",encoding="utf_8_sig")

sources_permutation_df = pd.DataFrame({'Sources':enriched_all_df.source.unique()})
sources_permutation_df.to_csv("Sources.csv",encoding="utf_8_sig")

for source in dataSourcesAll:
    sources_permutation_df[source] = sources_permutation_df.Sources.str.find(source)>-1

sources_permutation_df = pd.melt(sources_permutation_df,id_vars='Sources', var_name='Source', value_name='exists')
sources_permutation_df = sources_permutation_df[sources_permutation_df.exists==True]
sources_permutation_df[['Sources','Source']].to_csv("SourcesToSource.csv",encoding="utf_8_sig")


#
##=============================================================================================
## Merge 1st & 2nd datasets
##=============================================================================================
#df1 = chargingStations_PlugShare_df
#df2 = chargingStations_HERE_df
#file = folder + "/Fuzzy Merged CSVs/" + country + '_PlugShare_HERE'
#df_match1 = merge_datasets(df1,df2,coordinates,string_ids,non_ids,distance_threshold=get_thresholds(country,0,folder),string_threshold=get_thresholds(country,1,folder),isFirst=True,fileName=file) 
#df_match1.to_csv(file+'_Merged_All.csv')
#
##=============================================================================================
## Merge 3rd dataset
##=============================================================================================
#df1 = df_match1
#df2 = chargingStations_OpenStreetMap_df
#file = folder + "/Fuzzy Merged CSVs/" + country + '_PlugShare_HERE_OpenStreetMap'
#df_match2 = merge_datasets(df1,df2,coordinates,string_ids,non_ids,distance_threshold=get_thresholds(country,2,folder),string_threshold=get_thresholds(country,3,folder),isFirst=False,fileName=file) 
#df_match2.to_csv(file+'_Merged_All.csv')
#    
##=============================================================================================
## Merge 4th dataset
##=============================================================================================
#df1 = df_match2
#df2 = chargingStations_OpenChargeMap_df
#file = folder + "/Fuzzy Merged CSVs/" + country + '_PlugShare_HERE_OpenStreetMap_OpenChargeMap'
#df_match3 = merge_datasets(df1,df2,coordinates,string_ids,non_ids,distance_threshold=get_thresholds(country,4,folder),string_threshold=get_thresholds(country,5,folder),isFirst=False,fileName=file) 
#df_match3.to_csv(file+'_Merged_All.csv')
#
##=============================================================================================
## Merge 5th dataset
##=============================================================================================
#df1 = df_match3
#df2 = chargingStations_NewMotion_df
#file = folder + "/Fuzzy Merged CSVs/" + country + '_PlugShare_HERE_OpenStreetMap_OpenChargeMap_NewMotion'
#df_match4 = merge_datasets(df1,df2,coordinates,string_ids,non_ids,distance_threshold=get_thresholds(country,4,folder),string_threshold=get_thresholds(country,5,folder),isFirst=False,fileName=file) 
#df_match4.to_csv(file+'_Merged_All.csv')
#
##=============================================================================================
## Merge 6th dataset
##=============================================================================================
#df1 = df_match4
#df2 = chargingStations_PlugSurfing_df
#file = folder + "/Fuzzy Merged CSVs/" + country + '_PlugShare_HERE_OpenStreetMap_OpenChargeMap_NewMotion_PlugSurfing'
#df_match5 = merge_datasets(df1,df2,coordinates,string_ids,non_ids,distance_threshold=get_thresholds(country,4,folder),string_threshold=get_thresholds(country,5,folder),isFirst=False,fileName=file) 
#df_match5.to_csv(file+'_Merged_All.csv')

