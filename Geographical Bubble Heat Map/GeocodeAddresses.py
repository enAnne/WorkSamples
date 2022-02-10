# -*- coding: utf-8 -*-
"""
Created on Sat May 30 08:29:11 2020

@author: EEANNNG
"""

import pandas as pd
import glob
import HEREGeoCodeAPI
import os
import urllib.parse
import folium
from folium import plugins
from folium.plugins import HeatMap
from bokeh.plotting import figure
from bokeh.io import output_file, show


"""
==================================================================================================================
 Geocode customers address
==================================================================================================================
"""
folder = r'C:\Users\EEANNNG\My Stuff\CASE\Engagements\Adhoc\Dealer Network/'
customers = pd.read_excel(folder+'Indonesia Customers 2.xlsx')
all_address = customers[['Address','Country']].drop_duplicates(subset='Address').reset_index().drop(columns='index').reset_index()
all_address['Address'] = all_address.Address.str.replace('\\n', ", ").str.replace('\t', " ")
address_file_name = "all_address"
address_txt_name = address_file_name + ".txt"
address_csv_name = address_file_name + ".csv"
address_file = folder + address_csv_name
if len(glob.glob(address_txt_name)) > 0 : os.remove(folder+address_txt_name)
all_address.rename(columns={'index':'recId','Address':'searchText','Country':'country'}).to_csv(address_file, index=None, sep='\t', encoding='utf-8')

"""
!! Please read: !!
# 1. Manually rename the "all_address.csv" to "all_address.txt"
# 2. Get off office network
# 3. Run the "run_HERE_API" code
# 4. Pause and wait for the API to run in the background. 
# 5. After ~1 minute, run the "checkStatus_HERE_API" code to check if it is completed. 
#     In the beginning it will show all 0's': 
#        Status : accepted
#        TotalCount : 0
#        ...
#     When completed, it will show:
#        Status : completed
#        TotalCount : XXXX
#        ErrorCount : XXXX
# 6. After completed, continue running the remaining code which will google geocode the remaining addresses that were in ErrorCount
# 7. Remember to set getCoordinates = False after this is done
"""
# Run the HERE Maps GeoCoding to retrieve the coordinates for the addresses
response = HEREGeoCodeAPI.run_HERE_API(folder,address_txt_name)
# Check status of HERE API call
HEREGeoCodeAPI.checkStatus_HERE_API(folder,response)

# Obtain the results back from the result_*.txt file returned by HERE maps
# recId is important to match back to the query all_address.txt file
list_of_files = glob.glob(folder+'result_*.txt') 
HERE_resultFile = max(list_of_files, key=os.path.getctime)
[os.remove(x) for x in list_of_files if x != HERE_resultFile]
all_address_temp = pd.read_csv(HERE_resultFile, sep='\t')
all_address_temp = all_address_temp[['recId','displayLatitude','displayLongitude']].groupby('recId',as_index=False).mean()
all_address = pd.merge(all_address,all_address_temp,left_on='index',right_on='recId',how='left')

# Process remaining addresses missed by HERE, using GoogleAPI 
all_address_leftover = all_address[pd.isna(all_address.displayLatitude)]
leftover = len(all_address_leftover)
for i, r in all_address_leftover.iterrows():
    address_parsed = urllib.parse.quote(str(r.Address) + " " + str(r.Country))
    leftover = leftover-1
    print(leftover)    
    r = requests.get('https://maps.googleapis.com/maps/api/geocode/json?address='+address_parsed+"&key=AIzaSyCV8uJxTzwSg_P4LT_aiAMLRsd-dfCeMoA")
    json_data = r.json() 
    if len(json_data['results']) > 0:
        all_address.loc[i,'displayLatitude'] = json_data['results'][0]['geometry']['location']['lat']
        all_address.loc[i,'displayLongitude'] = json_data['results'][0]['geometry']['location']['lng']

# Save to a static file that can be retrieved from in future
all_address.info()
all_address.to_csv(address_file, encoding="utf8")

all_address = pd.read_csv(address_file, encoding="utf8")

customers2 = pd.merge(customers,all_address,on='Address',how='left')
customers2 = customers2[['Id', 'NrVehicles', 'Year', 'Address_Type__c', 'Address', 'displayLatitude', 'displayLongitude']]
customers2.rename(columns={'displayLatitude':'Latitude','displayLongitude':'Longitude'}, inplace=True)
customers2.info()

customers2.to_csv(folder+'Customers Geocoded.csv')

"""
==================================================================================================================
 Folium map
==================================================================================================================
"""

import urllib.request, json 
with urllib.request.urlopen("https://raw.githubusercontent.com/rifani/geojson-political-indonesia/master/IDN_adm_2_kabkota.json") as url:
    state_geo = json.loads(url.read().decode())
    
with urllib.request.urlopen("https://raw.githubusercontent.com/deldersveld/topojson/master/countries/denmark/denmark-municipalities.json") as url:
    state_geo2 = json.loads(url.read().decode())



coordinate_df = customers2[['displayLatitude', 'displayLongitude']]
coordinate_df = coordinate_df.dropna()
coordinates_list = [[row['displayLatitude'],row['displayLongitude']] for index, row in coordinate_df.iterrows()]

m = folium.Map(location=[-2,118], zoom_start=5)
HeatMap(data=coordinates_list, 
        min_opacity=0.5, 
        max_zoom=18, 
        max_val=1.0, 
        radius=4, 
        blur=1, 
        gradient=None, 
        overlay=True, 
        control=True, 
        show=True).add_to(m)
m.save('index.html')


from bokeh.plotting import figure
from bokeh.io import output_file, show

# Create the figure: p
p = figure(x_axis_label='fertility (children per woman)', y_axis_label='female_literacy (% population)')

# Use the circle marker glyph to plot the figure p
p.circle(fertility, female_literacy)

# Call the output_file() function and specify the name of the file
output_file('fert_lit.html')

# Display the plot
show(p)