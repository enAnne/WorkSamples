# -*- coding: utf-8 -*-
"""
Created on Thu Jul  4 11:29:32 2019

@author: EEANNNG
"""

import numpy as np
import pandas as pd
import countryBoundingBoxes as bb
import json
import requests
from requests.auth import HTTPProxyAuth
import random
import matplotlib

def get_user_agent():
  user_agent_list = [
   #Chrome
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    #Firefox
    'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)']
  return random.choice(user_agent_list)


def get_random_colors(getNames=True, getHexs=False, getRGBs=False):
    colors = []
    for name, hexC in matplotlib.colors.cnames.items():
        color = name if getNames == True else ( hexC if getHexs == True else ( matplotlib.colors.to_rgb(hexC) ) )
        colors.append(color)
    random.shuffle(colors)
    return colors

def get_session():
    s = requests.Session()
    s.proxies = {"http":"S633K0000003.my633.corpintra.net:3128", "https":"S633K0000003.my633.corpintra.net:3128"}
    s.trust_env=False
    s.headers['User-Agent']= get_user_agent()
    #s.auth = HTTPProxyAuth(user,password)
    return s
    
def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

def search_string_in_DF_columns(mystring,df):
    return df.columns[df.columns.str.lower().str.find(mystring.lower())>-1]
    
def search_string_in_CSV_columns(mystring,file,separator=",",encoding="utf-8"):
    df = pd.read_csv(file, sep = separator, nrows=1, encoding=encoding)
    return search_string_in_DF_columns(mystring,df)

def search_exact_string_in_DF(mystring,df):
    return (df == mystring).sum()[(df == mystring).sum() > 0]    

def search_string_in_DF(mystring,df):
    return df.columns[[(sum(df[x].astype(str).str.lower().str.find(mystring.lower())>-1) >0) for x in df ]] 

def read_csv(file,separator=","):
    return pd.read_csv( file, sep = separator, encoding='ISO-8859-1')

def write_dfs_to_xlsx_sheets(df_list, sheet_list, file_name):
    writer = pd.ExcelWriter(file_name,engine='xlsxwriter')   
    for dataframe, sheet in zip(df_list, sheet_list):
        dataframe.to_excel(writer, sheet_name=sheet, startrow=0 , startcol=0)   
    writer.save()
    
def read_xlsx_sheets_into_dfs(sheets_list, file_name, is_first_col_index=True):
    xls = pd.ExcelFile(file_name)
    if is_first_col_index:
        if isinstance(sheets_list,str) :
            df_list = xls.parse(sheets_list,index_col=0)
        else:
            df_list = [xls.parse(x,index_col=0) for x in sheets_list]    
    else:
        if isinstance(sheets_list,str) :
            df_list = xls.parse(sheets_list)
        else:
            df_list = [xls.parse(x) for x in sheets_list]   
    return df_list
    
def full_info(df):
    pd.set_option('display.max_columns', None) 
    pd.set_option('display.max_colwidth', -1)
    df = df.reindex(columns=sorted(df.columns))
    return df.info(verbose=True, null_counts=True)

def get_country_bounding_box(countryCode):
    """Returns countryLatitudeMin,countryLatitudeMax,countryLongitudeMin,countryLongitudeMax"""
    country_bounding_boxes_df = bb.country_bounding_boxes_df[bb.country_bounding_boxes_df.countryCode==countryCode]
    countryLatitudeMin,countryLatitudeMax,countryLongitudeMin,countryLongitudeMax = 0,0,0,0
    if country_bounding_boxes_df.shape[0] > 0:
        index = country_bounding_boxes_df.index[0]
        countryLatitudeMin = country_bounding_boxes_df.at[index,'lat1']
        countryLatitudeMax = country_bounding_boxes_df.at[index,'lat2']
        countryLongitudeMin = country_bounding_boxes_df.at[index,'lon1']
        countryLongitudeMax = country_bounding_boxes_df.at[index,'lon2']
    return countryLatitudeMin,countryLatitudeMax,countryLongitudeMin,countryLongitudeMax
    
def get_country_bounding_box_stepsize(countryCode,step_distance):
    """Returns latShiftSize,lonShiftSize"""
    countryLatitudeMin,countryLatitudeMax,countryLongitudeMin,countryLongitudeMax = get_country_bounding_box(countryCode)
    country_bounding_boxes_df = bb.country_bounding_boxes_df[bb.country_bounding_boxes_df.countryCode==countryCode]
    index = country_bounding_boxes_df.index[0]
    nrLatShifts = np.floor( country_bounding_boxes_df.at[index,'latitude_dist'] / step_distance )
    nrLonShifts = np.floor( country_bounding_boxes_df.at[index,'longitude_dist'] / step_distance )
    latShiftDegrees = (countryLongitudeMax-countryLongitudeMin)/nrLonShifts 
    lonShiftDegrees = (countryLatitudeMax-countryLatitudeMin)/nrLatShifts 
       
    return latShiftDegrees,lonShiftDegrees
    
def get_country_code(country,codeDigits=2):
    countries_df = read_csv(r"C:\Users\EEANNNG\WORK\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\Charging Stations Project\Data Reference\CountryCodes.csv")
    if codeDigits==2:
        return countries_df.Alpha2[countries_df.Country==country].iloc[0]
    else:
        return countries_df.Alpha3[countries_df.Country==country].iloc[0]
    
def get_country(country_code):
    countries_df = read_csv(r"C:\Users\EEANNNG\WORK\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\Charging Stations Project\Data Reference\CountryCodes.csv")
    if len(country_code)==2:
        return countries_df.Country[countries_df.Alpha2==country_code].iloc[0]
    else:
        return countries_df.Country[countries_df.Alpha3==country_code].iloc[0]

def get_providers_for_country(country):
    providers = read_csv(r"C:\Users\EEANNNG\WORK\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\Charging Stations Project\Data Reference\General_Providers.csv")
    providers = providers[(providers.Country=="All") | (providers.Country==country) ]
    return providers
