# -*- coding: utf-8 -*-
"""
Created on Wed Nov 14 14:50:55 2018

@author: user
"""

import numpy as np
import string

# Set the number of teams, must be an even number
# The number of clues and locations needed = Number of teams + 1
numberOfTeams = 10
numberOfClues = numberOfTeams + 1

teams = np.array(list(string.ascii_lowercase)[:numberOfTeams])
treasureHunt = np.ones(shape=(numberOfClues,numberOfClues))

for i in range(numberOfClues):
    for j in range(numberOfClues):
        treasureHunt[(i*j+i)%numberOfClues,i] = j+1

treasureHunt = np.flip(treasureHunt[:,1:].astype(int)).astype(str)        
treasureHuntBoard = np.vstack((teams,treasureHunt))

print('You may have up to ' + str(numberOfTeams) + ' teams -> ' + str(teams))
print('You will need ' + str(numberOfClues) + ' locations.' )
print('Location 0 is the starting point, where you hand out the first clue to every team.' )
print('Location ' + str(numberOfClues) + ' is the finishing point that everyone gathers back at.' )
print('Therefore, no clues will be placed at Location 0 or Location ' + str(numberOfClues) + '.')
for i in range(numberOfClues):    
    location = np.where(treasureHunt==str(i)) if i != 0 else np.where(treasureHunt==str(numberOfClues))
    hand_or_place = ', place clues ' if i != 0 else ', hand out clues '
    clues = []
    for index,j in enumerate(location[1][:]):
        next_clue_row = ( location[0][index] + 1 ) % numberOfClues        
        next_clue = treasureHunt[next_clue_row,j]
        clues.append(str(teams[j]) + next_clue) 
    print('At Location ' + str(i) + hand_or_place + str(clues))

