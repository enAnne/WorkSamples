"""
Created on Tue Jan 14 16:10:00 2020

Steps:
1. Export PowerBI desktop to Template
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

folder = r"C:\Users\eeann\OneDrive\Career\Mercedes Benz\Engagements\Engagements\Sales Funnel\Template/"
pbix_name = "Sales Funnel"
pbit = folder + pbix_name + '.pbit'
templateFolder = folder + pbix_name 

#===================================================================================
# Prepare files from PBIT template file
#===================================================================================
with zipfile.ZipFile(pbit, 'r') as zip_ref:
    zip_ref.extractall(templateFolder)

dataModelSchema = templateFolder + '/DataModelSchema'
dataModelSchemaFile = templateFolder + '/DataModelSchema.txt'

f= open(dataModelSchema,'r', encoding="UTF-16LE")
content= f.read()
f.close()
f= open(dataModelSchemaFile,'w', encoding="utf-8")
f.write(content)
f.close()
            
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

model_tables_fields.to_csv("Formulas.csv")

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

relationships_tables_fields_from = relationships.loc[relationships.IsValid,['fromTable','From']].rename(columns={'fromTable':'Table','From':'Naming'})
relationships_tables_fields_to = relationships.loc[relationships.IsValid,['toTable','To']].rename(columns={'toTable':'Table','To':'Naming'})
relationships_tables_fields_all = pd.concat([relationships_tables_fields_from,relationships_tables_fields_to])
relationships_tables_fields_all = relationships_tables_fields_all.drop_duplicates()

#===================================================================================
# Get all tables and columns used in visuals
#===================================================================================
def find_by_key(data, target):
    for key, value in data.items():
        if isinstance(value, dict):
            yield from find_by_key(value, target)
        elif key == target:
            yield value
            
jsonfile = open(layoutFile, encoding="utf-8", errors="surrogateescape")
reportPages = json.load(jsonfile)['sections']

allVisuals = []
visuals_tables_fields_all = pd.DataFrame()
for p, page in enumerate(reportPages):
    pageName = page['displayName']
    #print("Page: ", p, "-", pageName)
    
    # page = reportPages[1] # For zooming into single page
    for i,visualCategory in enumerate(page['visualContainers']):
        
        # visualCategory = page['visualContainers'][8] # For zooming into single visual
        config = json.loads(visualCategory['config'])
        # Only 2 types of configs: singleVisualGroup and singleVisual
        if 'singleVisual' in config.keys(): 
            visual = config['singleVisual']
            visualType = visual['visualType']
            allVisuals.append(visualType)
            
            table = []
            field = []
            # Exclude visuals without any field bindings
            if visualType not in (['actionButton','basicShape','image','textbox']):
                table_mapping = pd.DataFrame(visual['prototypeQuery']['From'])
                tables_fields = pd.DataFrame()
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
                tables_fields['Visual'] = visualType + '-' + str(i)
                table_mapping = table_mapping.set_index('Name')
                tables_fields['Table'] = tables_fields.Table.map(table_mapping.Entity)
                visuals_tables_fields_all = pd.concat([visuals_tables_fields_all,tables_fields])
            
visuals_tables_fields_all = visuals_tables_fields_all.drop_duplicates()        
       
# Get all visual types used in the dashboard
set(allVisuals)


#===================================================================================
# Get all base tables and columns used in visuals and relationships
#===================================================================================

def find_base_field(table, field, all_table_fields):
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
        all_table_fields.append(table_field)
        valueType = model_tables_fields.loc[model_tables_fields.Naming==table_field,'ValueType'].values[0]
        table = model_tables_fields.loc[model_tables_fields.Naming==table_field,'Table'].values[0]
        formula = model_tables_fields.loc[model_tables_fields.Naming==table_field,'Formula'].values[0]
        if valueType in ['measure','calculated']:
            referenced_columns = list(set(re.findall( "[a-zA-Z\d_']*\[.*?\]", formula)))
            for column in referenced_columns:
                yield from find_base_field(table, column, all_table_fields)
        elif valueType == 'tableColumn':
            yield table_field
                    
visuals_tables_fields = visuals_tables_fields_all[['Table','Column']].drop_duplicates()
visuals_tables_fields = pd.merge(visuals_tables_fields,model_tables_fields,on=['Table','Column'],how='left')
visuals_tables_fields = visuals_tables_fields.dropna(subset=['DataType'])

base_table_fields = []
all_table_fields = []

for i,field in visuals_tables_fields.iterrows():
    for table_field in find_base_field(field.Table,field.Naming,all_table_fields):
        base_table_fields.append(table_field)

for i,field in relationships_tables_fields_all.iterrows():
    for table_field in find_base_field(field.Table,field.Naming,all_table_fields):
        base_table_fields.append(table_field)
      

print( """
  ============================================================================
     Base table columns
  ============================================================================""")
base_table_fields = pd.DataFrame({'Naming':base_table_fields}).drop_duplicates()
base_table_fields = pd.merge(base_table_fields,model_tables_fields,on='Naming',how='left')
for table in sorted(base_table_fields.Table.unique()):
    print( "--------------------------------------------------------------------------")
    print( "Table : ", table )
    print( "Columns : '"+"','".join(base_table_fields.loc[base_table_fields.Table==table,'Column'])+"'")

print( """
 ============================================================================
     All columns
 ============================================================================""")
all_table_fields = pd.DataFrame({'Naming':all_table_fields}).drop_duplicates()
all_table_fields = pd.merge(all_table_fields,model_tables_fields,on='Naming',how='left')    
for table in sorted(all_table_fields.Table.unique()):
    print( "--------------------------------------------------------------------------")
    print( "Table : ", table )
    print( "Columns : '"+"','".join(all_table_fields.loc[all_table_fields.Table==table,'Column'])+"'")    
    
table = 'CalenderDate' 
field = 'CalenderDate[Datekey]'
        
base_table_fields.to_csv(folder+"Used_DataFields.csv")
all_table_fields.to_csv(folder+"Used_AllFields.csv")
model_tables_fields.to_csv(folder+"AllFields_Catalogue.csv")
