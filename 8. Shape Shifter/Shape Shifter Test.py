# -*- coding: utf-8 -*-
"""
Created on Fri Feb 25 13:45:55 2022

@author: eeann
"""

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import openpyxl
import time
from gekko import GEKKO
import itertools

"""=================================================================
# Defining Variables and Constraints
================================================================="""
start = time.time()

file= r'C:\Users\eeann\OneDrive\Documents\GitHub\WorkSamples\8. Shape Shifter/Test Game 2.xlsx'

target = 3
board_rows = 3
board_cols = 3
cells = pd.read_excel(file,sheet_name='Cells', engine="openpyxl")
shapes_block = pd.read_excel(file,sheet_name='Shapes_Block', engine="openpyxl")
shapes_block = shapes_block[shapes_block.block==1]
shapes = shapes_block[['shape_nr','rows','cols']].drop_duplicates()
shapes['max_row'] = board_rows - shapes.rows
shapes['max_col'] = board_cols - shapes.cols

# Variables
lists = [list(shapes.shape_nr), list(range(0,board_rows)), list(range(0,board_cols))]
shapes_cell = pd.DataFrame(list(itertools.product(*lists)), columns=['shape_nr', 'row', 'col'])
shapes_cell['max_row'] = shapes_cell.shape_nr.map(shapes.set_index('shape_nr').max_row)
shapes_cell['max_col'] = shapes_cell.shape_nr.map(shapes.set_index('shape_nr').max_col)
shapes_cell = shapes_cell[(shapes_cell.row <= shapes_cell.max_row) & (shapes_cell.col <= shapes_cell.max_col)]
# When a shape is assigned to a cell, only the first blocks is clicked on the board
shapes_cell['var_s_c'] = "var_s" + shapes_cell.shape_nr.astype(str) + '_c' + shapes_cell.row.astype(str) + "-" + shapes_cell.col.astype(str)
# When a shape is assigned to a cell, the other blocks in the shape will be assigned to other cells
shapes_block_cell = pd.merge(shapes_block[['shape_nr','i','j']], shapes_cell[['shape_nr','row','col']], on='shape_nr', how='outer')
shapes_block_cell['assigned_row'] = shapes_block_cell['row'] + shapes_block_cell['i']
shapes_block_cell['assigned_col'] = shapes_block_cell['col'] + shapes_block_cell['j']
shapes_block_cell['var_s_c_b'] = "var_s" + shapes_block_cell.shape_nr.astype(str) + "_c" + shapes_block_cell.row.astype(str) + "-" + shapes_block_cell.col.astype(str) + '_b' + shapes_block_cell.assigned_row.astype(str) + "-" + shapes_block_cell.assigned_col.astype(str)
shapes_block_cell['var_s_c'] = "var_s" + shapes_block_cell.shape_nr.astype(str) + "_c" + shapes_block_cell.row.astype(str) + "-" + shapes_block_cell.col.astype(str)

# Constraints
# Constraint 1. Each shape is assigned to only 1 cell; For every shape: sum(var_s_c) = 1
shapes_cell['value'] = 1
indexes = [x for x in list(shapes_cell.columns) if x not in ['var_s_c','value']]
constraint_1 = shapes_cell.pivot_table(index=indexes, columns='var_s_c', values= 'value', aggfunc='sum')
constraint_1 = constraint_1.reset_index().fillna(0)
constraint_1 = constraint_1.groupby('shape_nr',as_index=False).sum()
constraint_1['RHS'] = 1

# Constraint 2. If a shape is assigned to a cell, every block is assigned to subsequent cells; For every shape-cell-block: var_s_c_b = var_s_c
shapes_block_cell['value'] = 1
indexes = [x for x in list(shapes_block_cell.columns) if x not in ['var_s_c','value']]
constraint_2 = shapes_block_cell.pivot_table(index=indexes, columns='var_s_c', values= 'value', aggfunc='sum')
constraint_2['value'] = -1
constraint_2 = constraint_2.reset_index().fillna(0)
indexes = [x for x in list(constraint_2.columns) if x not in ['var_s_c_b','value']]
constraint_2 = constraint_2.pivot_table(index=indexes, columns='var_s_c_b', values= 'value', aggfunc='sum')
constraint_2 = constraint_2.reset_index().fillna(0)
constraint_2['RHS'] = 0

# Constraint 3. Every cell's assignments should add up to the target sequence; For every cell: var_c + sum(var_s_c_b) = target * int_c
shapes_block_cell['var_c'] = "var_c" + shapes_block_cell.assigned_row.astype(str) + "-" + shapes_block_cell.assigned_col.astype(str)
shapes_block_cell['value'] = 1
indexes = [x for x in list(shapes_block_cell.columns) if x not in ['var_s_c_b','value']]
constraint_3 = shapes_block_cell.pivot_table(index=indexes, columns='var_s_c_b', values= 'value', aggfunc='sum')
constraint_3 = constraint_3.reset_index().fillna(0)
constraint_3 = constraint_3.groupby('var_c',as_index=False).sum()
constraint_3['value'] = 1
constraint_3['var_c_int'] = constraint_3.var_c + '_int'
indexes = [x for x in list(constraint_3.columns) if x not in ['var_c','value']]
constraint_3 = constraint_3.pivot_table(index=indexes, columns='var_c', values= 'value', aggfunc='max')
constraint_3 = constraint_3.reset_index().fillna(0)
constraint_3['value'] = -target
indexes = [x for x in list(constraint_3.columns) if x not in ['var_c_int','value']]
constraint_3 = constraint_3.pivot_table(index=indexes, columns='var_c_int', values= 'value', aggfunc='max')
constraint_3 = constraint_3.reset_index().fillna(0)
constraint_3['RHS'] = 0 

# Combine all Constraints
constraints = pd.concat([constraint_1,constraint_2,constraint_3]).fillna(0)
variables = [x for x in list(constraints.columns) if x.find('var')==0]
coefficients = constraints[variables].values
RHS = constraints.RHS.values
weights = np.ones(len(variables))

end = time.time()
print("Defining Variables/Constraints:", end-start)

# Run solver
# Define Linear Programming Solver
m = GEKKO(remote=False)
x = m.Array(m.Var,len(variables),value=0,lb=0,ub=1,integer=True)
#m.qobj(weights,x=x,otype='max') # Objective function
for i,var in enumerate(variables):
    if var.find('var_c')==0 and var.find('int')>0:
        x[i].upper = 10000
    elif var.find('var_c')==0:
        init = cells.loc[cells.var_c==var,'seq'].values[0]
        x[i].value = init
        x[i].lower = init
        x[i].upper = init
        print("Initial", var, "=", init)
m.axb(coefficients,RHS,x=x,etype='=')
m.options.solver = 1
m.options.MAX_ITER = 100
m.options.MAX_TIME = 100000
#m.options.COLDSTART = 2
m.solve(disp=True)
end = time.time()
# m.open_folder()
print("Solution found:", m.options.APPSTATUS)
if m.options.APPSTATUS == 0:
    print("Reason: ",m.options.APPINFO)
print("Run solver:", end-start)

results = pd.DataFrame({"var":variables,"result":x}).set_index('var')
results['result'] = results.result.apply(lambda x:x.value[0])
results = results[results.result==1]
shapes_cell['result'] = shapes_cell.var_s_c.map(results.result)
shapes_cell_chosen = shapes_cell.dropna(subset=['result'])
for i,shape_cell in shapes_cell_chosen.iterrows():
    row = shape_cell.row
    col = shape_cell.col
    print("Var:", shape_cell.var_s_c)