# -*- coding: utf-8 -*-
"""
Created on Fri Mar 22 10:57:43 2019

@author: EEANNNG
"""

from os import chdir
chdir(r"C:\Users\eeann\OneDrive\Documents\GitHub\WorkSamples\Database Summary")
import ExploreData as ed
import os

"""
#========================================================================================================================
# Sample explore_sql_table of SFDC data
#========================================================================================================================
"""  
server = "ssfrazubsea0001.database.windows.net"
db = "ADW_MB_PRD_SIT"
schema = "ADW_SFDC_TGT"
user = "eeannng"
pw = "zCupTQWLcgdgW7nstN4Jh7ZNQeYU"

table = "ADDRESS__C"
ed.explore_sql_table(server, db, schema, table, user, pw, True, printInfo=False, where = "CHARINDEX('Thailand',COUNTRY__C) > 0", fileName="Thailand_ADDRESS")
table = "ACCOUNT"
ed.explore_sql_table(server, db, schema, table, user, pw, True, printInfo=False, where = "CHARINDEX('Thailand',COUNTRY__C) > 0", fileName="Thailand_ACCOUNT")
table = "ACCOUNT_LINK__C"
ed.explore_sql_table(server, db, schema, table, user, pw, True, printInfo=False, where = "CHARINDEX('Thailand',RETAIL_COUNTRY__C) > 0", fileName="Thailand_ACCOUNT_LINK")
table = "CASE"
ed.explore_sql_table(server, db, schema, table, user, pw, True, printInfo=False, fileName="Korea_CASE")
table = "CAR_MODEL__C"
ed.explore_sql_table(server, db, schema, table, user, pw, True, printInfo=False, fileName="Korea_CAR_MODEL")
table = "LEAD__C"
ed.explore_sql_table(server, db, schema, table, user, pw, True, printInfo=False, fileName="Korea_LEAD")
table = "CAMPAIGN"
ed.explore_sql_table(server, db, schema, table, user, pw, True, printInfo=False, fileName="Korea_CAMPAIGN")
table = "CAMPAIGN_MEMBER__C" # "CAMPAIGN_LEAD__C", "CAMPAIGN_CITY__C", "CAMPAIGN_OFFERING__C", "CAMPAIGN_PACKAGE__C", "CAMPAIGN_PARTNER__C" are empty
ed.explore_sql_table(server, db, schema, table, user, pw, True, printInfo=False, fileName="Korea_CAMPAIGN_MEMBER")
table = "CAMPAIGNMEMBER"
ed.explore_sql_table(server, db, schema, table, user, pw, True, printInfo=False, fileName="Korea_CAMPAIGNMEMBER")
table = "RETAIL_CAMPAIGN__C"
ed.explore_sql_table(server, db, schema, table, user, pw, True, printInfo=False, fileName="Korea_RETAIL_CAMPAIGN")
table = "RETAIL_CAMPAIGN_MEMBER__C"
ed.explore_sql_table(server, db, schema, table, user, pw, True, printInfo=False, fileName="Korea_RETAIL_CAMPAIGN_MEMBER")
table = "RETAIL_TASK__C"
ed.explore_sql_table(server, db, schema, table, user, pw, True, printInfo=False, fileName="Korea_RETAIL_TASK")
table = "BOOKING__C"
ed.explore_sql_table(server, db, schema, table, user, pw, True, printInfo=False, fileName="Korea_BOOKING")
table = "VEHICLE__C"
ed.explore_sql_table(server, db, schema, table, user, pw, True, printInfo=False, where = "CHARINDEX('KR',Market__c) > 0", fileName="Korea_VEHICLE")
table = "VEHICLE_RELATIONSHIP__C"
ed.explore_sql_table(server, db, schema, table, user, pw, True, printInfo=False, where = "CHARINDEX('KR',Market__c) > 0", fileName="Korea_VEHICLE_RELATIONSHIP")
table = "CAMPAIGN"
ed.explore_sql_table(server, db, schema, table, user, pw, True, printInfo=False, fileName="Korea_CAMPAIGN")

"""
#========================================================================================================================
# Sample explore_sql_table for SWT data in localhost
#========================================================================================================================
"""  
folder = r"C:\Users\EEANNNG\My Stuff\CASE\SWT"
chdir(folder)

server = "C633L0007S6T2X2\SQLEXPRESS"
db = "SWT"
schema = "dbo"

table = "KNA1"
columns_csv = r"C:\Users\EEANNNG\My Stuff\CASE\SWT\KNA1_columns.csv"
ed.explore_sql_table(server, db, schema, table, printInfo=False, fileName=table, columns_csv = columns_csv)

table = "KNVV"
columns_csv = r"C:\Users\EEANNNG\My Stuff\CASE\SWT\KNVV_columns.csv"
ed.explore_sql_table(server, db, schema, table, printInfo=False, fileName=table, columns_csv = columns_csv)

table = "VLCVEHICLE"
columns_csv = r"C:\Users\EEANNNG\My Stuff\CASE\SWT\VLCVEHICLES_columns.csv"
ed.explore_sql_table(server, db, schema, table, printInfo=False, fileName=table, columns_csv = columns_csv)

"""
#========================================================================================================================
# Sample explore_csv_table for Malaysia SFDC CSV files
#========================================================================================================================
"""

folder = r"C:\Users\EEANNNG\My Stuff\CASE\EQ Score\eq-hot-leads-crm\Malaysia\SFDC Raw"
chdir(folder)

filePath = folder + "\SFDC_ACCOUNT.csv"
ed.explore_csv_table(filePath, printInfo=False, sep="|", fileName="SFDC_ACCOUNT") 

filePath = folder + "\SFDC_ADDRESS.csv"
ed.explore_csv_table(filePath, printInfo=False, sep="|", fileName="SFDC_ADDRESS") 

filePath = folder + "\SFDC_CAR_MODEL.CSV"
ed.explore_csv_table(filePath, printInfo=False, sep="\t", fileName="SFDC_CAR_MODEL")

filePath = folder + "\SFDC_RETAIL_TASK.CSV"
ed.explore_csv_table(filePath, printInfo=False, sep="|", fileName="SFDC_RETAIL_TASK")  

filePath = folder + "\SFDC_VEHICLE.csv"
ed.explore_csv_table(filePath, printInfo=False, sep="|", fileName="SFDC_VEHICLE")  

filePath = folder + "\SFDC_VEHICLE_RELATIONSHIP.csv"
ed.explore_csv_table(filePath, printInfo=False, sep="|", fileName="SFDC_VEHICLE_RELATIONSHIP")  

filePath = folder + "\SFDC_CASE_MY.CSV"
ed.explore_csv_table(filePath, printInfo=False, sep="|", fileName="SFDC_CASE_MY")  

filePath = folder + "\SFDC_Campaign_MY.CSV"
ed.explore_csv_table(filePath, printInfo=False, sep="|", fileName="SFDC_CAMPAIGN_MY")  

filePath = folder + "\SFDC_CampaignMember_MY.CSV"
ed.explore_csv_table(filePath, printInfo=False, sep="|", fileName="SFDC_CAMPAIGN_MEMBER_MY")  

"""
#========================================================================================================================
# Sample explore_csv_table for charging
#========================================================================================================================
"""

folder = r"C:\Users\EEANNNG\WORK\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\Charging Stations Project"
filePath = folder+"/CSVs/EAnywhere/Thailand_Processed.csv"
ed.explore_csv_table(filePath, printInfo=False, sep=",", encoding = "utf_8_sig", fileName="EAnywhere")  

filePath = r"C:\Users\EEANNNG\WORK\CASE\EQ Score\eq-hot-leads-crm\Charging Stations Code\HERE maps data RO.csv"
ed.explore_csv_table(filePath, printInfo=False, sep=",", fileName="HERE_Maps")  


"""
#========================================================================================================================
# Sample explore_dataframe for in memory df
#========================================================================================================================
"""
import pandas as pd
# Explore all columns in tables
folder = r'C:\Users\eeann\OneDrive\Learn\Data Science\Teach Python\Business - Original 2/'
for file in os.listdir(folder):
    if file.find('.csv') > -1:
        fileName = folder + file
        objectName = file.replace(".csv","")
        df = pd.read_csv(fileName)
        ed.explore_dataframe(df, printInfo = True, fileName=objectName)
