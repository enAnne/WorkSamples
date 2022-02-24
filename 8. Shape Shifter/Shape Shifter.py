# -*- coding: utf-8 -*-
"""
Created on Wed Feb 23 17:16:27 2022

@author: eeann
"""

import time
import pandas as pd
import numpy as np
import datetime 
import itertools
from gekko import GEKKO
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException, WebDriverException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

def getElement(driver,eType,eString,tWait=0,maxWait=10):
    if tWait > 0:
        time.sleep(tWait)
    wait = WebDriverWait(driver, maxWait)
    return wait.until(EC.element_to_be_clickable((eType,eString)))

def getElements(driver,eString,tWait=0,maxWait=10):
    if tWait > 0:
        time.sleep(tWait)
    wait = WebDriverWait(driver, maxWait)
    wait.until(EC.element_to_be_clickable((By.XPATH,eString)))
    return driver.find_elements_by_xpath(eString)

def elementExists(driver,eType,eString,tWait=0,maxWait=10):
    try: 
        getElement(driver,eType,eString,tWait,maxWait) 
    except TimeoutException:
        return False
    return True

def getPiece(img_src):
    return img_src.replace("https://images.neopets.com/medieval/shapeshifter/","").replace(".gif","")
    
# Open browser
driver = webdriver.Firefox(executable_path=r"C:\Users\eeann\AppData\Local\Microsoft\WindowsApps\geckodriver.exe")
driver.maximize_window()
# Login to Neopets account
driver.get("https://www.neopets.com")
getElement(driver,By.XPATH,"//button[text()='Login']").click()
getElement(driver,By.NAME,"username").send_keys('enAnne') 
getElement(driver,By.NAME,'password').send_keys('en900804') 
getElement(driver,By.XPATH,"//input[@id='loginButton']").click()
# Go to ShapeShifter page
time.sleep(2)
driver.get("https://www.neopets.com/medieval/shapeshifter.phtml")

def start_game(loop = True):
    
    """=================================================================
    # Getting Puzzle
    ================================================================="""
    start = time.time()
    
    # Get the Pieces sequence
    pieces = []
    for e in getElements(driver,"//table/tbody/tr/td[2]/center[2]/table/tbody/tr/td/table/tbody/tr/td/img"):
        piece = getPiece(e.get_attribute("src"))
        if piece != 'arrow':
            pieces.append(piece)
    pieces.pop()
    pieces = pd.DataFrame({"piece":pieces, "seq":list(range(1,len(pieces)+1))})
    target = pieces.seq.iloc[-1]
    
    # Get the Board
    board_size = len(getElements(driver,"//table/tbody/tr/td/p/table/tbody/tr"))
    cells = []
    for i in range(0,board_size):
        for j in range(0,board_size):
            piece = getElement(driver,By.NAME,'i'+str(j)+'_'+str(i)).get_attribute("src")
            piece = getPiece(piece)
            cell = {"i":i, "j":j, "piece":piece}
            cells.append(cell)
    cells = pd.DataFrame(cells)
    cells['seq'] = cells.piece.map(pieces.set_index('piece').seq)
    cells['var_c'] = "var_c" + cells.i.astype(str) + "-" + cells.j.astype(str)
    
    # Get the Shapes
    nrShapes = len(getElements(driver,"//table/tbody/tr/td[2]/center[3]/center/table/tbody/tr/td")) + 1
    shapes_block = []
    for s in range(0,nrShapes):
        path = "//table/tbody/tr/td[2]/center[3]/center/table/tbody/tr["+str((s-1)//8+1)+"]/td["+str((s-1)%8+1)+"]/table/tbody/"
        if s == 0:
            path = "//table/tbody/tr/td[2]/center[3]/p/table/tbody/tr/td/table/tbody/"
        rows = len(getElements(driver, path+"tr"))
        cols = len(getElements(driver, path+"tr[1]/td"))
        for i in range(0,rows):
            for j in range(0,cols):
                block = getElement(driver,By.XPATH, path+"tr["+str(i+1)+"]/td["+str(j+1)+"]").get_attribute("innerHTML") != ''
                shape_block = {"shape_nr":s, "rows":rows, "cols":cols, "i":i, "j":j, "block":int(block)}
                shapes_block.append(shape_block)
    shapes_block = pd.DataFrame(shapes_block)
    shapes_block = shapes_block[shapes_block.block==1]
    shapes = shapes_block[['shape_nr','rows','cols']].drop_duplicates()
    shapes['max_row'] = board_size - shapes.rows
    shapes['max_col'] = board_size - shapes.cols
    
    end = time.time()
    print("Get puzzle pieces:", end-start)
        
    """=================================================================
    # Creating solver
    ================================================================="""
    start = time.time()

    # Variables
    lists = [list(shapes.shape_nr), list(range(0,board_size)), list(range(0,board_size))]
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
    
    # Define Linear Programming Solver
    m = GEKKO(remote=False)
    x = m.Array(m.Var,len(variables),value=0,lb=0,ub=100,integer=True)
    m.qobj(weights,x=x,otype='max') # Objective function
    for i,var in enumerate(variables):
        if var.find('var_c')==0 and var.find('int')>0:
            x[i].upper = 200
        elif var.find('var_c')==0:
            init = cells.loc[cells.var_c==var,'seq'].values[0]
            x[i].value = init
            x[i].lower = init
            x[i].upper = init
    m.axb(coefficients,RHS,x=x,etype='=')
    m.options.solver = 1
    m.options.MAX_ITER = 100
    
    end = time.time()
    print("Create solver:", end-start)
    
    """=================================================================
    # Run solver
    ================================================================="""
    # Run Solver
    start = time.time()
    m.solve(disp=False)
    end = time.time()
    print("Run solver:", end-start)
    
    """=================================================================
    # Play Game
    ================================================================="""
    start = time.time()
    a = ActionChains(driver)
    for var,ass in zip(variables,x):
        if ass.value[0] > 0.5:
            shape_cell = shapes_cell.loc[shapes_cell.var_s_c==var]
            if len(shape_cell) > 0:
                row = shape_cell.row.values[0]
                col = shape_cell.col.values[0]
                print('i'+str(col)+'_'+str(row))
                e = getElement(driver,By.NAME,'i'+str(col)+'_'+str(row))
                a.move_to_element(e).perform()
                e.click()
    end = time.time()
    print("Play game:", end-start)
    
    if loop:
        getElement(driver,By.XPATH,"//input[@value='Move to the next level?!']").click()
        time.sleep(1)
        start_game()

start_game(loop = True)










