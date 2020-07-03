# -*- coding: utf-8 -*-
"""
Created on Sun Aug 11 19:41:06 2019

@author: EEANNNG
"""

import tabula
import pandas as pd
from PyPDF2 import PdfFileReader
from string import digits

# P3 pdf file
folder = r"C:\Users\EEANNNG\Work\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\Charging Stations Project\PowerBI\Market Analysis"
pdf = folder + r"\20181002_Daimler_P3_Market-Analysis-Charging-Infrastructure.pdf"
pdff = PdfFileReader(open(pdf,'rb'))
pages_total = pdff.getNumPages()

# Table dimensions containing Provider Analysis (AC,DC counts)
height = 4.97
width = 8.87
top = 1.8
left = 0.43
area=[x*72 for x in [top,left,top+height,left+width]]

# Header dimensions containing Country name
header_height = 0.52
header_width = 4.25
header_area=[0,0]+[x*72 for x in [header_height,header_width]]

# Get tables and header from each page, save into lists of DataFrames
dfs=[]
headers=[]
for page in range(0,pages_total):
    df = tabula.read_pdf(pdf,guess=False,stream=False,encoding="utf-8",area=area,multiple_tables=True,pages=page+1)
    header = tabula.read_pdf(pdf,guess=False,stream=False,encoding="utf-8",area=header_area,multiple_tables=True,pages=page+1)
    #If you want to change the table by editing the columns you can do that here.
    if((len(df)==1) and (df[0].shape[0]>0)):
        print(page,len(df))
        if(df[0].iloc[0,0] == "CPO"):
            dfs=dfs+[df[0]] #again you can choose between merge or concat as per your need
            headers=headers+[header[0]] 

# Clean up data from each table and concatenate into 1 dataframe
df_all = pd.DataFrame()
for header,df in zip(headers,dfs):
    df = df.iloc[2:,0:3] # Remove first 2 rows and keep first 3 columns
    df = df.dropna(subset=[0]) # Remove empty rows
    df.columns = ["Provider","AC","DC"]
    df['Country'] = header.iloc[0,0][12:] # Add country information
    df_all = pd.concat([df_all,df])
df_all = df_all[df_all['Provider']!='Total']
df_all['Provider'] = df_all['Provider'].str.lstrip(digits)

df_all.to_csv(folder+"/P3_Data.csv",encoding='utf_8_sig')
