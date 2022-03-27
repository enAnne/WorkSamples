# -*- coding: utf-8 -*-
"""
Created on Wed Mar 16 14:25:00 2022

@author: eeann
"""

import pandas as pd
import numpy as np
import os
import glob
os.chdir(r'C:\Users\eeann\OneDrive\Documents\GitHub\Python-Repo/')
import Utils

os.chdir(r'C:\Users\eeann\OneDrive\Career\M1\Legacy + New Stack Analysis.worksheet\Worksheet TMLs/')
file_name = 'Worksheet.xlsx'

""" =================================================================
 # Get Tables/Views Joins
================================================================= """
pattern = '*.view.tml'
view_files = glob.glob(pattern)
pattern = '*.table.tml'
table_files = glob.glob(pattern)

foreign_keys = []
primary_keys = []
for file in view_files+table_files:
    with open(file) as f:
        lines = f.readlines()
    if any([l.find('"on":')>-1 for l in lines]):
        join_on = lines[[l.find('"on":')>-1 for l in lines].index(True)]
        f_key = join_on.split('] = [')[0].replace('"on": "[','').replace('"on": "([','').replace("\\r\\n", "").strip()
        f_key = {'table':f_key.split('::')[0],'fkey':f_key.split('::')[1]}
        foreign_keys.append(f_key)
        p_key = join_on.split('] = [')[1].replace(']"','').replace('])"','').replace("\\r\\n", "").strip()
        p_key = {'table':p_key.split('::')[0],'pkey':p_key.split('::')[1]}
        primary_keys.append(p_key)
foreign_keys = pd.DataFrame(foreign_keys).drop_duplicates()   
primary_keys = pd.DataFrame(primary_keys).drop_duplicates() 

""" =================================================================
 # Get Tables and Views SQL
================================================================= """
views = pd.read_excel(file_name, sheet_name='view_def')
worksheet_columns = pd.read_excel(file_name, sheet_name='worksheet_columns')

for file in view_files:
    with open(file) as f:
        lines = f.readlines()
    name = lines[2].replace('name:','').strip()
    formulas = [l.find('formulas:')>-1 for l in lines]
    col_disp = []
    # if any([l.find('formulas:')>-1 for l in lines]):
    #     pst_formulas = [l.find('formulas:')>-1 for l in lines].index(True)
    #     pst_search_query = [l.find('search_query:')>-1 for l in lines].index(True)
    #     col_disp = [l.replace('- id:','').strip() for l in lines[pst_formulas+1:pst_search_query] if l.find('- id:')>-1]
    pst_columns = [l.find('view_columns:')>-1 for l in lines].index(True)
    joins = [l.find('joins_with:')>-1 for l in lines]
    pst_joins = joins.index(True) if any(joins) else len(lines)
    col_disp = col_disp + [l.replace('- name:','').strip() for l in lines[pst_columns+1:pst_joins] if l.find('- name:')>-1]
    view_cols = pd.DataFrame({'col_disp':col_disp})
    view_cols['table'] = name
    view_cols['col_renamed'] = view_cols.set_index(['table','col_disp']).index.map(worksheet_columns.dropna(subset=['table']).set_index(['table','column'])['name'])
    view_cols['col_renamed'] = view_cols['col_renamed'].fillna(view_cols.col_disp)
    view_cols.reset_index(inplace=True)
    view_cols['id'] = 'ca_' + (view_cols['index']+1).astype(str)
    view_cols = view_cols.set_index('id').to_dict()['col_renamed']
    views.loc[views.name==name,'sql_proper'] = views.loc[views.name==name,'SQL'].replace(view_cols,regex=True)
    
for file in table_files:
    with open(file) as f:
        lines = f.readlines()
    name = lines[2].replace('name:','').strip()
    table_name = lines[3].replace('db:','').strip()+'.'+lines[4].replace('schema:','').strip()+'.'+lines[5].replace('db_table:','').strip()
    pst_columns = [l.find('columns:')>-1 for l in lines].index(True)
    joins = [l.find('joins_with:')>-1 for l in lines]
    pst_joins = joins.index(True) if any(joins) else len(lines)
    col_disp = [l.replace('db_column_name:','').strip() for l in lines[pst_columns+1:pst_joins] if l.find('db_column_name:')>-1]
    col_disp = [x for x in col_disp if x in list(worksheet_columns.loc[worksheet_columns.table==name,'column'])]
    table_cols = pd.DataFrame({'col_disp':col_disp})
    table_cols['table'] = name
    table_cols['col_renamed'] = table_cols.set_index(['table','col_disp']).index.map(worksheet_columns.dropna(subset=['table']).set_index(['table','column'])['name'])
    table_cols['col_renamed'] = table_cols['col_renamed'].fillna(table_cols.col_disp)
    table_cols['col_renamed'] = table_cols.col_disp.astype(str) + ' "' + table_cols.col_renamed.astype(str) + '"'
    views.loc[views.name==name,'sql_proper'] = 'select ' + ','.join(list(table_cols.col_renamed)) + ' from ' + table_name

with open('(SC_TS) View Last Bill Plan Billing.txt', 'r') as file:
    sql = file.read().replace('\n', ' ')
    views.loc[views['name']=='(SC_TS) View Last Bill Plan Billing','sql_proper'] = sql
with open('(SC_TS) View Last VAS Billing.txt', 'r') as file:
    sql = file.read().replace('\n', ' ')
    views.loc[views['name']=='(SC_TS) View Last VAS Billing','sql_proper'] = sql
    
writeToExcel(file_name,'sql',views,header=True,index=False,row=0,col=0,title='',overwrite=True)
    
""" =================================================================
 # Get Worksheet Data Model (Tables, Columns, Relationships)
================================================================= """
with open('Legacy + New Stack Analys.worksheet.tml') as f:
    lines = f.readlines()
    
pst_tables = [l.find('tables:')>-c1 for l in lines].index(True)
pst_joins = [l.find('joins:')>-1 for l in lines].index(True)
pst_table_paths = [l.find('table_paths:')>-1 for l in lines].index(True)
pst_formulas = [l.find('formulas:')>-1 for l in lines].index(True)
pst_worksheet_columns = [l.find('worksheet_columns:')>-1 for l in lines].index(True)
last = len(lines)

def convert_table(pst_field,pst_next_field):
    nl_field = [l.find('  -')==0 for l in lines[pst_field+1:pst_next_field]]
    field = pd.DataFrame({'NewLine':nl_field,'Data':lines[pst_field+1:pst_next_field]})
    field.reset_index(inplace=True)
    field.loc[field.NewLine,'LineNr'] = field.loc[field.NewLine,'index']
    field = field.drop(columns=['NewLine','index'])
    field['LineNr'] = field['LineNr'].fillna(method='ffill')
    field['Type'] = [d[0:d.find(':')].replace(' ','').replace('-','') for d in field.Data]
    field['Data'] = [d[d.find(':')+2:] for d in field.Data]
    field.loc[field['Data'].str.find('     - ')==0,'Type'] = np.nan
    field['Data'] = field['Data'].str.replace('     - ','')
    need_grouping = any(pd.isna(field['Type']))
    field['Type'] = field['Type'].fillna(method='ffill')
    if need_grouping:
        field = field.groupby(['LineNr','Type'],as_index=False).Data.apply(lambda x:','.join(x))
    field = field.groupby('LineNr').apply(lambda d: dict(zip(d['Type'], d['Data']))).apply(pd.Series)
    return field

tables = convert_table(pst_tables,pst_joins)
joins = convert_table(pst_joins,pst_table_paths)
table_paths = convert_table(pst_table_paths,pst_formulas)
formulas = convert_table(pst_formulas,pst_worksheet_columns)
formulas['id'] = formulas['id'].fillna(formulas['name'])
worksheet_columns = convert_table(pst_worksheet_columns,last)
worksheet_columns['name'] = worksheet_columns['name'].str.replace("\\r\\n", "").str.replace("'", "").str.replace('"', "").str.strip()
worksheet_columns['formula'] = worksheet_columns['formula_id'].map(formulas.set_index('id').expr)
worksheet_columns['table'] = worksheet_columns['column_id'].str.split('::').str[0].str.replace('_1','').str.replace("\\r\\n", "").str.replace("'", "").str.replace('"', "").str.strip()
worksheet_columns['column'] = worksheet_columns['column_id'].str.split('::').str[1].str.replace("\\r\\n", "").str.replace("'", "").str.replace('"', "").str.strip()
worksheet_columns = worksheet_columns[['column_type','name','table','column','synonyms','formula','aggregation','calendar','index_type','format_pattern','is_bypass_rls','join_progressive']]

worksheet_columns['pkey'] = worksheet_columns.set_index(['table','column']).index.isin(primary_keys.set_index(['table','pkey']).index)
worksheet_columns['fkey'] = worksheet_columns.set_index(['table','column']).index.isin(foreign_keys.set_index(['table','fkey']).index)
worksheet_columns['type_name'] = '(' + worksheet_columns['column_type'].str[0] + ') ' + worksheet_columns['name']

writeToExcel(file_name,'tables',tables,header=True,index=False,row=0,col=0,title='',overwrite=True)
writeToExcel(file_name,'joins',joins,header=True,index=False,row=0,col=0,title='',overwrite=True)
writeToExcel(file_name,'table_paths',table_paths,header=True,index=False,row=0,col=0,title='',overwrite=True)
writeToExcel(file_name,'formulas',formulas,header=True,index=False,row=0,col=0,title='',overwrite=True)
writeToExcel(file_name,'worksheet_columns',worksheet_columns,header=True,index=False,row=0,col=0,title='',overwrite=True)

sql = ''
for t in worksheet_columns.table.dropna().unique():
    sql = sql + 'CREATE TABLE ' + t + '\n(\n' + ',\n'.join(worksheet_columns.loc[worksheet_columns.table==t,'type_name']) + '\n);\n'







