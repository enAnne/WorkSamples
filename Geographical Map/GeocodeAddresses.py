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