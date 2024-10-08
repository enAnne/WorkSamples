"""
Created on Tue Jan 14 16:10:00 2020

Steps:
1. Export PowerBI desktop to Template, save into same location as PBIX file.
2. Extract pbit file into folder called "Template"
3. Put pbit file into "Template" folder
4. Set foler path below
5. Set pbix_name below
 
@author: EEANNNG
"""

import json
import pandas as pd
import re
import zipfile
import PySimpleGUI as sg
from PySimpleGUI import InputCombo, Combo, Multiline, ML, MLine, Checkbox, CB, Check, Button, B, Btn, ButtonMenu, Canvas, Column, Col, Combo, Frame, Graph, Image, InputText, Input, In, Listbox, LBox, Menu, Multiline, ML, MLine, OptionMenu, Output, Pane, ProgressBar, Radio, Slider, Spin, StatusBar, Tab, TabGroup, Table, Text, Txt, T, Tree, TreeData,  VerticalSeparator, Window, Sizer

#folder = r"C:\Users\eeann\OneDrive\Career\Mercedes Benz\Engagements\Engagements\Sales Funnel\Template/"
#pbix_name = "Sales Funnel"
        
def evaluateUsage(pbix_name,folder):
    #===================================================================================
    # Prepare files from PBIT template file
    #===================================================================================
    outputFolder = folder + r'/Evaluate Power BI Template/'
    templateFolder = outputFolder + '/Others'
    pbit = folder + pbix_name + '.pbit'
    with zipfile.ZipFile(pbit, 'r') as zip_ref:
        zip_ref.extractall(templateFolder)
    
    # DataModelSchema file contains the Data Model (Tables, Relationships)
    dataModelSchema = templateFolder + '/DataModelSchema'
    dataModelSchemaFile = templateFolder + '/DataModelSchema.txt'
    
    f= open(dataModelSchema,'r', encoding="UTF-16LE")
    content= f.read()
    f.close()
    f= open(dataModelSchemaFile,'w', encoding="utf-8")
    f.write(content)
    f.close()
          
    # Layout file contains the Dashboard UI (Charts, Filters)
    layout = templateFolder + '/Report/Layout'
    layoutFile = templateFolder + '/Report/Layout.txt'
    
    f= open(layout,'r', encoding="UTF-16LE")
    content= f.read()
    f.close()
    f= open(layoutFile,'w', encoding="utf-8")
    f.write(content)
    f.close()
    
    #===================================================================================
    # Get all tables and columns loaded in the model
    #===================================================================================
    jsonfile = open(dataModelSchemaFile, encoding="utf-8", errors="surrogateescape")
    tables = json.load(jsonfile)['model']['tables']
    
    model_tables_fields = pd.DataFrame()
    for x in tables:    
        tableName = x['name']
        # For Calculated Tables, the formula is on Table level
        table_formula = ''
        if x['partitions'][0]['source']['type'] == 'calculated':
            table_formula = x['partitions'][0]['source']['expression']
    
        # For Measures, the formula is on Column level
        if 'measures' in x:
            for m in x['measures']:
                column = m['name']
                vtype = 'measure'
                dtype = '' if 'dataType' not in m else m['dataType']
                formula = m['expression']
                model_tables_fields = model_tables_fields.append({'Table':tableName,'Column':column,'DataType':dtype,'ValueType':vtype,'Formula':formula, 'Hidden':False},ignore_index=True)
        # For Calculated Columns, the formula is on Column level
        for c in x['columns']:
            isHidden = 'isHidden' in c
            column = c['name']
            dtype = '' if 'dataType' not in c else c['dataType']
            vtype = 'tableColumn' if 'type' not in c else c['type']      
            formula = table_formula if isHidden | (vtype in ['tableColumn','calculatedTableColumn']) else c['expression']
            model_tables_fields = model_tables_fields.append({'Table':tableName,'Column':column,'DataType':dtype,'ValueType':vtype,'Formula':formula, 'Hidden':isHidden},ignore_index=True)
    
    model_tables_fields['Naming'] = model_tables_fields['Table'] + '[' + model_tables_fields['Column'] + ']'    
    model_tables_fields = model_tables_fields.sort_values('Naming')
    
    #===================================================================================
    # Get all tables and columns used in relationships
    #===================================================================================
    jsonfile = open(dataModelSchemaFile, encoding="utf-8", errors="surrogateescape")
    relationships = json.load(jsonfile)['model']['relationships']
    
    relationships = pd.DataFrame(relationships)
    relationships['From'] = relationships.fromTable + '[' + relationships.fromColumn + ']' 
    relationships['To'] = relationships.toTable + '[' + relationships.toColumn + ']' 
    
    # Some deleted relationships still remain in model
    relationships['From_Valid'] = relationships['From'].map(model_tables_fields.set_index('Naming')['Hidden']) == 0
    relationships['To_Valid'] = relationships['To'].map(model_tables_fields.set_index('Naming')['Hidden']) == 0
    relationships['IsValid'] = relationships['From_Valid'] & relationships['To_Valid']
    
    relationships_tables_fields_from = relationships.loc[relationships.IsValid,['fromTable','From','From','To']]
    relationships_tables_fields_from.columns = ['Table','Naming','From','To']
    relationships_tables_fields_to = relationships.loc[relationships.IsValid,['toTable','To','From','To']]
    relationships_tables_fields_to.columns = ['Table','Naming','From','To']
    relationships_tables_fields_all = pd.concat([relationships_tables_fields_from,relationships_tables_fields_to])
    relationships_tables_fields_all = relationships_tables_fields_all.drop_duplicates()
    
    #===================================================================================
    # Get all tables and columns used in visuals and filters
    #===================================================================================
    # Recursive function, calls itself to identify a nested key within the value of a key
    def find_by_key(data, target):
        for key, value in data.items():
            if isinstance(value, dict):
                yield from find_by_key(value, target)
            elif key == target:
                yield value
                
    jsonfile = open(layoutFile, encoding="utf-8", errors="surrogateescape")
    reportPages = json.load(jsonfile)['sections']
    
    allVisuals = []
    pagefilters_tables_fields_all = pd.DataFrame()
    visuals_tables_fields_all = pd.DataFrame()
    for p, page in enumerate(reportPages):
        pageName = page['displayName']
        
        pagefilters = []
        for i,filter_exp in enumerate(json.loads(page['filters'])):
            pagefilter = {'Page':pageName,'Table':filter_exp['expression']['Column']['Expression']['SourceRef']['Entity'],'Column':filter_exp['expression']['Column']['Property']}
            pagefilters.append(pagefilter)
        pagefilters_tables_fields_all = pd.concat([pagefilters_tables_fields_all,pd.DataFrame(pagefilters)])
            
        # page = reportPages[1] # For zooming into single page
        for i,visualCategory in enumerate(page['visualContainers']):
            
            # visualCategory = page['visualContainers'][8] # For zooming into single visual
            config = json.loads(visualCategory['config'])
            # Only 2 types of configs: singleVisualGroup and singleVisual
            if 'singleVisual' in config.keys(): 
                visual = config['singleVisual']
                visualType = visual['visualType']
                # Only visuals whose Title is set in Selection pane will have this value
                try:
                    title = visual['vcObjects']['title'][0]['properties']['text']['expr']['Literal']['Value']   
                except:
                    title = ''
                allVisuals.append(visualType)
                        
                table = []
                field = []
                # Exclude visuals without any field bindings
                if visualType not in (['shape','actionButton','basicShape','image','textbox']):
                    # visual['prototypeQuery']['From'] contains the table names in code
                    table_mapping = pd.DataFrame(visual['prototypeQuery']['From'])
                    tables_fields = pd.DataFrame()
                    # visual['prototypeQuery']['Select'] references the table names using code
                    for bindingPurpose in visual['prototypeQuery']['Select']:
                        for x in find_by_key(bindingPurpose, "Source"):
                            table.append(x)
                        for x in find_by_key(bindingPurpose, "Property"):
                            field.append(x)
                        for x in find_by_key(bindingPurpose, "Level"):
                            if x not in ['Year','Quarter','Month','Day']:
                                field.append(x)
                        #print(i, 'Visual:', visualType, '  Table:', table, 'Column:', field)  
                        tables_fields = pd.concat([tables_fields,pd.DataFrame({'Table':table,'Column':field})])
                    tables_fields['Page'] = pageName
                    tables_fields['Visual'] = title if title != '' else visualType
                    table_mapping = table_mapping.set_index('Name')
                    tables_fields['Table'] = tables_fields.Table.map(table_mapping.Entity)
                    visuals_tables_fields_all = pd.concat([visuals_tables_fields_all,tables_fields])
                
    visuals_tables_fields_all = visuals_tables_fields_all.drop_duplicates()        
           
    # Get all visual types used in the dashboard
    set(allVisuals)
    
    
    #===================================================================================
    # Get all base tables and columns used in visuals and relationships
    #===================================================================================
    # Recursive function, to find the final field used within a measure (recursively call itself when there is a measure within a measure)
    def find_base_field(table, field, used_table_fields):
        table_field = field
        if field[0] == "[":
            field = field.replace("[","").replace("]","")
            table_field = model_tables_fields.loc[(model_tables_fields.Table==table) & (model_tables_fields.Column==field),'Naming']
            if len(table_field) == 0:
                table_field = model_tables_fields.loc[(model_tables_fields.ValueType=='measure') & (model_tables_fields.Column==field),'Naming']
            if len(table_field) > 0:
                table_field = table_field.values[0]
        elif field[0] == "'":
            table_field = table_field.replace("'","")
        
        if len(table_field) > 0 and sum(model_tables_fields.Naming==table_field) > 0:
            used_table_fields.append(table_field)
            valueType = model_tables_fields.loc[model_tables_fields.Naming==table_field,'ValueType'].values[0]
            table = model_tables_fields.loc[model_tables_fields.Naming==table_field,'Table'].values[0]
            formula = model_tables_fields.loc[model_tables_fields.Naming==table_field,'Formula'].values[0]
            if valueType in ['measure','calculated']:
                referenced_columns = list(set(re.findall( "[a-zA-Z\d_']*\[.*?\]", formula)))
                for column in referenced_columns:
                    yield from find_base_field(table, column, used_table_fields)
            elif valueType == 'tableColumn':
                yield table_field
                        
    visuals_tables_fields = visuals_tables_fields_all[['Table','Column']].drop_duplicates()
    visuals_tables_fields = pd.merge(visuals_tables_fields,model_tables_fields,on=['Table','Column'],how='left')
    visuals_tables_fields = visuals_tables_fields.dropna(subset=['DataType'])
    
    base_table_fields = []
    used_table_fields = []
    
    for i,field in visuals_tables_fields.iterrows():
        for table_field in find_base_field(field.Table,field.Naming,used_table_fields):
            base_table_fields.append(table_field)
    
    for i,field in relationships_tables_fields_all.iterrows():
        for table_field in find_base_field(field.Table,field.Naming,used_table_fields):
            base_table_fields.append(table_field)
          
    base_table_fields = list(set(base_table_fields))
    used_table_fields = list(set(used_table_fields))
    
    model_tables_fields['UsedInVisuals'] = model_tables_fields.Naming.isin(used_table_fields)
    model_tables_fields['IsLoaded_UsedInVisuals'] = model_tables_fields.Naming.isin(base_table_fields)
    
    model_tables_fields.to_csv(outputFolder+"AllFields_Catalogue.csv", index=False)
    
#===================================================================================
# GUI to extract PBIT file
#===================================================================================

sg.theme('Dark Brown')
layout = [
            [sg.Text('PBIT File',justification="right",size=(13,1)), sg.In('',size=(31,1),key='-InputFile-'), sg.FileBrowse('Browse ',file_types=(("Power BI Template", "*.pbit"),))],
            [sg.Button('Evaluate')],
         ]
window = sg.Window('Evaluate Power BI Template', layout)

while True:
    event, values = window.Read(timeout=200)       # wait for up to 100 ms for a GUI event
    if event in (sg.WIN_CLOSED, 'Exit'):
        stop = True
        window.close()
        break
    elif event in ['Evaluate']:
        pbit = values['-InputFile-']
        folder = '/'.join(pbit.split('/')[:-1]) + '/'
        pbix_name = pbit.split('/')[-1].split('.')[0]
        evaluateUsage(pbix_name,folder)
        window.Close()

pbit = r'C:\Users\eeann\OneDrive\Career\Toptal\Bingham/DataModel 30 Sep.pbit'



