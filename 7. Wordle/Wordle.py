# -*- coding: utf-8 -*-
"""
Created on Mon Feb 21 14:16:32 2022

@author: eeann

Reference: https://apmonitor.com/wiki/index.php/Main/IntegerProgramming
Reference: https://gekko.readthedocs.io/en/latest/model_methods.html
"""

import pandas as pd
import numpy as np
import random
import string
from sklearn.preprocessing import MultiLabelBinarizer
from gekko import GEKKO
import time
import re

def choose_n_words(n=4,iters=30):
    alphabets = list(string.ascii_lowercase)
    five_letter_words = pd.read_csv(r"C:\Users\eeann\OneDrive\Documents\GitHub\WorkSamples\Wordle\All Wordle Words.csv")
    five_letter_words['Word'] = five_letter_words.Word.str.lower()
    five_letter_words['alphabets'] = five_letter_words.Word.apply(lambda x:list(x))
    
    mlb = MultiLabelBinarizer(sparse_output=True)
    five_letter_words = five_letter_words.join(pd.DataFrame.sparse.from_spmatrix(
                    mlb.fit_transform(five_letter_words.pop('alphabets')),
                    index=five_letter_words.index,
                    columns=mlb.classes_))
    five_letter_words = five_letter_words.set_index('Word')
    
    #five_letter_words = five_letter_words[five_letter_words.index.isin(['charm','chasm','crave','funky','juice','moist','stalk','world','wrong','zebra','wrong'])]
    five_letter_words = five_letter_words[five_letter_words.sum(axis=1)==5] # No repeating characters
    #five_letter_words = five_letter_words.sample(n=500, random_state=random.randint(1,1000)) # Narrow down the search space
    
    # Variables
    variables = alphabets + five_letter_words.index.tolist()
    nrWords = len(five_letter_words)
    nrAlphabets = len(alphabets)
    
    # Objective Function
    weights = five_letter_words.sum().rank().tolist() + nrWords*[0] 
    # Weight for each alphabet is its frequency in the English dictionary
    # Set a hard Constraint on NrWords - thus no need to give it a weight
    
    # Constraints:
    # 1. For every word: Sum(letter_asg[contained_in_word]) >= 5 * word_asg
    # 2. For every letter: Sum(word_asg[containing_letter]) >= letter_asg
    # 3. Sum(word_asg) <= 4
    coefficients_1 = np.append(five_letter_words.values,-np.identity(nrWords)*5,axis=1).tolist()
    coefficients_2 = np.append(-np.identity(nrAlphabets),five_letter_words.values.T,axis=1).tolist()
    coefficients_3 = [nrAlphabets * [0] + nrWords * [-1]]
    coefficients = coefficients_1 + coefficients_2 + coefficients_3
    RHS = (nrWords + nrAlphabets) * [0] + [-n]
    
    # Define Linear Programming Solver
    m = GEKKO(remote=False)
    x = m.Array(m.Var,nrWords+nrAlphabets,value=0,lb=0,ub=1,integer=True)
    m.qobj(weights,x=x,otype='max') # Objective function
    m.axb(coefficients,RHS,x=x,etype='>=')
    m.options.solver = 1
    m.options.MAX_ITER = iters
    
    # Run Solver
    start = time.time()
    m.solve(disp=False)
    end = time.time()
    
    # Results
    not_covered = [var for x_i, var in zip(m._variables,variables) if len(var) <= 1 and x_i[0] < 0.5]
    words = [var for x_i, var in zip(m._variables,variables) if len(var) > 1 and x_i[0] > 0.5]
    
    # Print Results
    print('Solution time: ', end - start)
    print(len(not_covered), "uncovered letters - ", not_covered)
    print(words)

def permutate_word(position='.....',confirm='',maybe='x'):
    five_letter_words = pd.read_csv(r"C:\Users\eeann\OneDrive\Documents\GitHub\WorkSamples\Wordle\All Wordle Words.csv")
    five_letter_words['Word'] = five_letter_words.Word.str.lower()
    alphabets = list(string.ascii_lowercase)
    confirmNot = list(set(alphabets) - set(confirm+maybe)) 
    five_letter_words = five_letter_words[five_letter_words.Word.apply(lambda x: re.findall(position, x) != [])]
    return five_letter_words[five_letter_words.Word.apply(lambda y: len(list(set(confirm)-set(y)))==0 and len(list(set(y)-set(confirmNot)))==len(set(y)))]
    
choose_n_words(5,100)
permutate_word('.....','poy','')
permutate_word(maybe='wfgjbxmaiu')
