# -*- coding: utf-8 -*-
"""
Created on Wed Feb 23 17:16:27 2022

https://developers.google.com/optimization/scheduling/employee_scheduling

@author: eeann
"""

import time
import pandas as pd
import numpy as np
import datetime 
import itertools
from ortools.linear_solver import pywraplp
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
    
def reopenBrowser():
    # Open browser
    driver = webdriver.Firefox(executable_path=r"C:\Users\eeann\AppData\Local\Microsoft\WindowsApps\geckodriver.exe")
    driver.maximize_window()
    # Login to Neopets account
    driver.get("https://www.neopets.com")
    time.sleep(2)
    getElement(driver,By.XPATH,"//button[text()='Login']").click()
    getElement(driver,By.NAME,"username").send_keys('enAnne') 
    getElement(driver,By.NAME,'password').send_keys('en900804') 
    getElement(driver,By.XPATH,"//input[@id='loginButton']").click()
    # Go to ShapeShifter page
    time.sleep(2)
    driver.get("https://www.neopets.com/medieval/shapeshifter.phtml")
    return driver

def start_game(driver, play = True, loop = False, force = False, max_iter=1000000, max_time=1000000):
    
    """=================================================================
    # Getting Puzzle
    ================================================================="""
    start = time.time()
    
    if elementExists(driver,By.XPATH,"//table/tbody/tr/td[2]/p[2]/table/tbody/tr[1]/td/b"):
        driver.get("https://www.neopets.com/medieval/shapeshifter.phtml")
        
    # Get the Pieces sequence
    pieces = []
    for e in getElements(driver,"//table/tbody/tr/td[2]/center[2]/table/tbody/tr/td/table/tbody/tr/td/img"):
        piece = getPiece(e.get_attribute("src"))
        if piece != 'arrow':
            pieces.append(piece)
    pieces.pop()
    pieces = pd.DataFrame({"piece":pieces, "seq":list(range(1,len(pieces)+1))})
    target = pieces.seq.iloc[-1]
    
    # Get the Board (level 40 and above)
    board_rows = len(getElements(driver,"/html/body/div[3]/div[3]/table/tbody/tr/td[2]/table/tbody/tr"))
    board_cols = len(getElements(driver,"/html/body/div[3]/div[3]/table/tbody/tr/td[2]/table/tbody/tr[1]/td"))
    # Get the Board (below level 40)
    #board_rows = len(getElements(driver,"//table/tbody/tr/td/p/table/tbody/tr"))
    #board_cols = len(getElements(driver,"//table/tbody/tr/td/p/table/tbody/tr[1]/td"))
    cells = []
    for i in range(0,board_rows):
        for j in range(0,board_cols):
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
            #path = "//table/tbody/tr/td[2]/center[3]/p/table/tbody/tr/td/table/tbody/" # below level 40
            path = "//table/tbody/tr/td[2]/center[3]/table/tbody/tr/td/table/tbody/" # above level 40
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
    shapes['max_row'] = board_rows - shapes.rows
    shapes['max_col'] = board_cols - shapes.cols
    
    end = time.time()
    print("Get puzzle pieces:", end-start)
        
    """=================================================================
    # Defining Variables and Constraints
    ================================================================="""
    start = time.time()
    #solver = pywraplp.Solver('Solve Puzzle', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    solver = pywraplp.Solver.CreateSolver('SCIP')
    
    # Define Variables in DataFrames
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
        
    # All shape_blocks assigned to a cell have to add up to a multiple of the target
    shapes_block_cell['var_c'] = "var_c" + shapes_block_cell.assigned_row.astype(str) + "-" + shapes_block_cell.assigned_col.astype(str)
    
    # Create Variables and Constraints
    # Constraint 1. Each shape is assigned to only 1 cell; For every shape: sum(var_s_c) = 1
    for s in shapes_cell.shape_nr.unique():
        vars_sc = []
        for sc in shapes_cell[shapes_cell.shape_nr==s].var_s_c:
            var_sc = solver.BoolVar(sc)
            vars_sc.append(var_sc)
        solver.Add( sum(vars_sc) == 1, 'const_1sc_per_s' + str(s))

    # Constraint 2. If a shape is assigned to a cell, every block is assigned to subsequent cells; For every shape-cell-block: var_s_c_b = var_s_c
    for sc in shapes_block_cell.var_s_c.unique():
        var_sc = solver.LookupVariable(sc)
        for scb in shapes_block_cell[shapes_block_cell.var_s_c==sc].var_s_c_b:
            var_scb = solver.BoolVar(scb)
            solver.Add( var_scb == var_sc, 'const_scb_if_sc' + str(scb))
    
    # Constraint 3. Every cell's assignments should add up to the target sequence; For every cell: c_init + sum(var_s_c_b) = target * var_c
    for c,cell in cells.iterrows():
        var_c = solver.IntVar(0,int(target+nrShapes),cell.var_c)
        vars_scb = []
        for scb in shapes_block_cell[shapes_block_cell.var_c==cell.var_c].var_s_c_b:
            vars_scb.append(solver.LookupVariable(scb))
        solver.Add( sum(vars_scb) + cell.seq == target * var_c, 'const_sum_scb_multiple_c' + str(c))
    
    end = time.time()
    print("Defining Variables/Constraints:", end-start)
    with open(r'C:\Users\eeann\OneDrive\Documents\GitHub\WorkSamples\8. Shape Shifter\Puzzle.txt', 'w') as f:
        f.write(solver.ExportModelAsLpFormat(False).replace('\\', '').replace(',_', ','))
    
    """=================================================================
    # Run solver
    ================================================================="""
    start = time.time()
    # Define Linear Programming Solver
    status = solver.Solve()
    
    # If an optimal solution has been found, print results
    if status == pywraplp.Solver.OPTIMAL:
      print('================= Solution =================')
      print(f'Solved in {solver.wall_time():.2f} milliseconds in {solver.iterations()} iterations')
    else:
      print('The solver could not find an optimal solution.')
      
    end = time.time()
    print("Run solver:", end-start)
    
    """=================================================================
    # Play Game
    ================================================================="""
    if play:
        start = time.time()
        a = ActionChains(driver)
        results = pd.DataFrame({"variable":solver.variables()})
        results['var'] = results.variable.apply(lambda x:x.name())
        results['result'] = results.variable.apply(lambda x:x.solution_value())
        results_viewable = results[['var','result']]
        results = results[results.result==1].set_index('var')
        shapes_cell['result'] = shapes_cell.var_s_c.map(results.result)
        shapes_cell_chosen = shapes_cell.dropna(subset=['result'])
        for i,shape_cell in shapes_cell_chosen.iterrows():
            row = shape_cell.row
            col = shape_cell.col
            print("Var:", shape_cell.var_s_c)
        for i,shape_cell in shapes_cell_chosen.iterrows():
            row = shape_cell.row
            col = shape_cell.col
            print("Placing shape:", shape_cell.shape_nr,'on i'+str(row)+'-j'+str(col))
            e = getElement(driver,By.NAME,'i'+str(col)+'_'+str(row))
            a.move_to_element(e).perform()
            e.click()
        end = time.time()
        print("Play game:", end-start)
    
    if loop:
        getElement(driver,By.XPATH,"//input[@value='Move to the next level?!']").click()
        time.sleep(2)
        start_game(driver, play, loop, force)

driver = reopenBrowser()
start_game(driver, play = True, loop = True, force = False)






