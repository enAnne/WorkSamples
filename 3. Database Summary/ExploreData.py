# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 14:44:55 2019 (IMPROVED VERSION)

@author: EEANNNG
"""

import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pylab
import pyodbc
from matplotlib.backends.backend_pdf import PdfPages

"""
#========================================================================================================================
# Set parameters for optimized analysis performance
#========================================================================================================================
"""
#plt.style.use('ggplot') # This is even uglier..
mpl.rcParams['font.size'] = 13.0
threshold_ExcludeFromAnalysis = 98 # Percentage of same values in a column to exclude it from analysis
maxLabelLength = 15 # The length of the columns labels to be displayed
nrColumnsToLoadEachTime = 5 # Each time loading from CSV/SQL table, it will load only 10 columns.
threshold_MaxNrCategories = 20 # The total number of categories in the column must be no more than 20, in order to be drawn as a pie chart
threshold_MinBiggestCategoryFraction = 0.2 # The biggest set in the column must be at least 20 percent of total, in order to be drawn as a pie chart
threshold_LowerPercentile = 2 # For histograms, limit x axis range to 2% - 98% percentile.
threshold_UpperPercentile = 98 # For histograms, limit x axis range to 2% - 98% percentile.

"""
#========================================================================================================================
# Function explore_table
#========================================================================================================================
"""
def explore_table_pdf (df, printInfo = True, fileName='Test', columns_csv = ''):    
    pdf = PdfPages('Analyze_'+fileName+'.pdf')
    columns_df = pd.DataFrame()
    explore_table (df, pdf, printInfo, columns_df )
    pdf.close()
    
def explore_table (df, pdf, printInfo = True, columns_df = pd.DataFrame()):        
    """
    This function will print the statistics of the columns in the dataframe passed in.
    The way in which statistics will be displayed:    
        - Boolean columns      => Pie Chart
        - Categorical columns  => Pie Chart
        - String columns       => Table
        - Numeric columns      => Histogram
        - Date/Time columns    => Histogram
    """
    df = df.reindex(columns=sorted(df.columns)) # Sort columns alphabetically
    
    if printInfo : # Only print the df.info() on the first batch
        print( df.info(verbose=True,null_counts=True) )
    
    for i, column in enumerate(df.columns): # Go through each column in the df, starting from currentPosition
        columnName = column
        print(column)
        columnNameToDisplay = column
        if (columns_df.shape[0]!= 0) and (column in columns_df.index): # If column naming lookup table is provided
            columnName = columns_df.loc[column].at['Name']
            columnNameToDisplay = column+":"+columnName
        columnStats = df[column].value_counts(normalize=True,dropna=False).to_frame() 
        nanPercentage = pd.isna(df[column]).sum() / len(df[column]) * 100
        nanPercentageString = "(" + round(nanPercentage,2).astype(str) + "% NaN's)"
        
        # Only display the column if it's values are not dominated by a single value like nan or False
        if ( round(columnStats[column].iloc[0],4) < threshold_ExcludeFromAnalysis / 100 if len(columnStats) > 0 else False): 
            # For categorical/string type columns, either draw pie charts or print statistics table
            if pd.notnull(df[column]).any() & ( (df[column].dtype=="object") | (df[column].dtype=="bool") ) :
                columnStats.index = columnStats.index.astype(str).str[0:maxLabelLength].str.rjust(maxLabelLength+5)
                
                # Draw pie charts for columns with less than X nr of categories
                if (len(columnStats) < threshold_MaxNrCategories) :
                    plt.figure(figsize=(9,4))
                    # Data to plot
                    labels = columnStats.index
                    sizes = columnStats[column]
                    patches, texts = plt.pie(sizes, shadow=True, startangle=140)
                    plt.legend(patches, labels, loc="best")
                    plt.axis('equal')
                    plt.title(str(i)+'. '+columnNameToDisplay+nanPercentageString)
                    pdf.savefig()
                    plt.close()
                # Otherwise, print statistics for the categories in the column.
                else: 
                    columnStats.reset_index(inplace=True)
                    columnStats[column] = round(columnStats[column]*100,2).astype(str) + "%" # Print percentage
                    columnStats = columnStats[0:8] # Print only top 8 rows of data stats
                    plt.figure(figsize=(9,2)) # Put dataframe in a figure so that it can be printed into PDF
                    ax=plt.subplot(111)
                    ax.title.set_text(str(i)+'. '+columnNameToDisplay) 
                    ax.axis('off')                    
                    r = columnStats.shape[0]
                    c = columnStats.shape[1]
                    table = ax.table(cellText=columnStats.values, colLabels=columnStats.columns, bbox=[0,0,1,1])
                    for key, cell in table.get_celld().items():
                        cell.set_linewidth(0)
                    pdf.savefig()
                    plt.close()
            
            # For numerical & date/time columns, draw histogram
            elif (df[column].dtype=="int") | (str(df[column].dtype).find("float")>-1) | (df[column].dtype=="<M8[ns]"):
                plt.figure(figsize=(9,4))
                percentileLower = df[column].dropna().quantile(0.01) # Remove negative outliers from the X axis range
                percentileUpper = df[column].dropna().quantile(0.99) # Remove positive outliers from the X axis range
                df[column][pd.notnull(df[column])] = df[column][pd.notnull(df[column])].apply(lambda x: min( max(x,percentileLower), percentileUpper) )   
                df[column][pd.notnull(df[column])].hist()            
                plt.title(str(i)+'. '+columnNameToDisplay+nanPercentageString)  
                pdf.savefig()
                plt.close()
            

"""
#========================================================================================================================
# Function explore_sql_table
#========================================================================================================================
"""
     
def explore_sql_table (server, db, schema, table, user="", pw="", needsLogin=False, cols = "*", where = "", printInfo=True, fileName='Test', columns_csv = ""):    
    """
    This function is the exact same as "explore_csv_table", but loads from an SQL table instead
    -> If there is a lookup file for the column names (in case the columns are codes), specify it as columns_csv. This file should contain the fields "Field" and "Name", where "Field" is to match with the column names in the SQL_table of interest.
    The flow of analysis is:
        1. Sort columns alphabetically
        2. Load nrColumnsToLoadEachTime of columns data from CSV (in case the data is too much)
        3. Send the dataframe into explore_table()
    """
    pp = PdfPages('Analyze_'+fileName+'.pdf')
    columns_df = pd.read_csv(columns_csv,index_col="Field") if columns_csv != "" else pd.DataFrame() # Lookup table for column naming

    if needsLogin:
        sql_conn = pyodbc.connect(driver='{ODBC Driver 17 for SQL Server}', server=server, database=db, UID=user, PWD=pw)
    else:
        # Ensure that "ODBC Driver 17 for SQL Server" is configured in my ODBC 
        sql_conn = pyodbc.connect(driver='{ODBC Driver 17 for SQL Server}', server=server, database=db, trusted_connection='yes')
    
    if where != "":
        where = "where " + where
        
    query_all = "SELECT TOP 1 " + cols + " FROM [" + schema + "].[" + table + "]" + where
    df_all = pd.read_sql(query_all, sql_conn)    
        
    df_all = df_all.reindex(columns=sorted(df_all.columns, key=lambda v: (v.upper(), v[0].islower()))) # Sort columns alphabetically
    totalNrColumns = len(df_all.columns)
    
    startPosition = 0
    while startPosition < totalNrColumns :
        columns = "],[".join(df_all.columns[startPosition:startPosition+nrColumnsToLoadEachTime])        
        query = "SELECT [" + columns +"] FROM [" + schema + "].[" + table + "]" + where
        df = pd.read_sql(query, sql_conn)
        
        explore_table(df, pp, printInfo, columns_df)         
        startPosition = nrColumnsToLoadEachTime + startPosition 
    
    pp.close()
    

"""
#========================================================================================================================
# Function explore_csv_table
#========================================================================================================================
"""
def explore_csv_table (filePath, cols = [], printInfo = True, sep = ",", encoding = 'utf-8', fileName='Test', columns_csv = ""):    
    """
    This function is the exact same as "explore_sql_table", but loads from a CSV table instead.
    -> If there is a lookup file for the column names (in case the columns are codes), specify it as columns_csv. This file should contain the fields "Field" and "Name", where "Field" is to match with the column names in the CSV_table of interest.
    The flow of analysis is:
        1. Sort columns alphabetically
        2. Load nrColumnsToLoadEachTime of columns data from CSV (in case the data is too much)
        3. Send the dataframe into explore_table()
    """

    pp = PdfPages('Analyze_'+fileName+'.pdf')
    columns_df = pd.DataFrame()
#    columns_df = pd.read_csv(columns_csv,index_col="Field") if columns_csv != "" else pd.DataFrame() # Lookup table for column naming
    
    df_all = pd.read_csv( filePath, sep = sep, usecols = cols, nrows = 1, encoding = encoding)
    if len(cols) == 0:
        df_all = pd.read_csv( filePath, sep = sep, nrows = 1, encoding = encoding)
        
    df_all = df_all.reindex(columns=sorted(df_all.columns)) # Sort columns alphabetically
    totalNrColumns = len(df_all.columns)
    
    startPosition = 0
    while startPosition < totalNrColumns :
        columns = df_all.columns[startPosition:startPosition+nrColumnsToLoadEachTime]
        df = pd.read_csv( filePath, sep = sep, usecols=columns, encoding = encoding)
        
        explore_table(df, pp, printInfo, columns_df)         
        startPosition = nrColumnsToLoadEachTime + startPosition 
    
    pp.close()    
    
    
"""
#========================================================================================================================
# Function explore_dataframe
#========================================================================================================================
"""
def explore_dataframe (df, cols = [], printInfo = True, fileName='Test', columns_csv = ""):    
    """
    This function is the exact same as "explore_sql_table", but loads from a CSV table instead.
    -> If there is a lookup file for the column names (in case the columns are codes), specify it as columns_csv. This file should contain the fields "Field" and "Name", where "Field" is to match with the column names in the CSV_table of interest.
    The flow of analysis is:
        1. Sort columns alphabetically
        2. Load nrColumnsToLoadEachTime of columns data from CSV (in case the data is too much)
        3. Send the dataframe into explore_table()
    """

    pp = PdfPages('Analyze_'+fileName+'.pdf')
    columns_df = pd.DataFrame()
#    columns_df = pd.read_csv(columns_csv,index_col="Field") if columns_csv != "" else pd.DataFrame() # Lookup table for column naming
    
    df = df.reindex(columns=sorted(df.columns)) # Sort columns alphabetically
    explore_table(df, pp, printInfo, columns_df)         
    
    pp.close()    























