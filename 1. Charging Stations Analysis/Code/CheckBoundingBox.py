# -*- coding: utf-8 -*-
"""
Created on Mon Jul 15 17:57:08 2019

@author: EEANNNG
"""

countries_df = read_csv(r"C:\Users\EEANNNG\WORK\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\Charging Stations Project\Data Reference\CountryCodes.csv")

countries_df['countryLatitudeMin'] = 0
countries_df['countryLatitudeMax'] = 0
countries_df['countryLongitudeMin'] = 0
countries_df['countryLongitudeMax'] = 0 

for i,row in countries_df.iterrows():
    print(row.Alpha2)
    countryLatitudeMin,countryLatitudeMax,countryLongitudeMin,countryLongitudeMax = get_country_bounding_box(row.Alpha2)
    countries_df.loc[i,'countryLatitudeMin'] = countryLatitudeMin
    countries_df.loc[i,'countryLatitudeMax'] = countryLatitudeMax
    countries_df.loc[i,'countryLongitudeMin'] = countryLongitudeMin
    countries_df.loc[i,'countryLongitudeMax'] = countryLongitudeMax
    
countries_df['hasBB'] = countries_df[['countryLatitudeMin','countryLatitudeMax','countryLongitudeMin','countryLongitudeMax']].sum(axis=1) != 0
countries_df = countries_df[countries_df['hasBB']]
countries_df['error'] = abs(countries_df['countryLatitudeMin'] - countries_df['latmin']) + abs(countries_df['countryLatitudeMax'] - countries_df['latmax']) + abs(countries_df['countryLongitudeMin'] - countries_df['longmin']) + abs(countries_df['countryLongitudeMax'] - countries_df['longmax'])

countries = ['Romania','Slovakia','Hungary','Turkey','Thailand','Malaysia','Singapore','Indonesia','Australia','New Zealand','India','United Arab Emirates','Russia']
countries_df = countries_df[countries_df.Country.apply(lambda x:x in countries)]

countries_df.Country.apply(lambda x:x in countries).sum()
