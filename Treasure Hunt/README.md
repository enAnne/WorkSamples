# Treasure Hunt
This is a treasure hunt clue-location assignment tool. This simple treasure hunt game is where multiple teams/players race against each other through the same locations but in different sequence until they reach the final destination, and there need not be fascillitators stationed at each location but just well sequenced clues at their locations.

# Challenge
When creating a treasure hunt game where there are multiple teams/players racing each other, the sequence of clues for every team should be different from all others, so that the different teams do not meet at a certain location and then start following each other through the rest of the game to reach the finish line. In short, the sequence has to prevent "copying" of other teams.

# Solution
Enter the number of teams in the game, and the python script will generate the assignment of clues to each location.
When printing the clues on paper, each team should have it's own color, and it should be the same color for all clues for a team.
An important rule - The winning teams has to have complete set of all clues in hand of their team's color - meaning if they reach the final destination without the complete set of clues or with clues that belong to other teams (different colors), the team will be forfeited. Should they cheat and skip the clue's sequence or take one of another team's, they will miss out on the sequence and eventually lose the game.

The excel file "TreasureHunt.xlsx" shows an example of how to set up the clues and locations for a treasure hunt game.
