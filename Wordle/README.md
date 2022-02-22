# Wordle
The New York Times game - https://www.nytimes.com/games/wordle/index.html

## Challenge
You have 6 tries to guess the correct word - so the 6th try should be the permutation of letters discovered in the first 5 tries.

Ideally, one is able to uncover all the correct letters in fewer tries.
So what are the best words to spend the first 3 guesses on?

## Solution
n = 3 

3 words that cover 15 alphabets - ['pithy', 'could', 'snare'] or ['itchy', 'paler', 'sound'] or ['crust', 'daily', 'phone'] or ['radio', 'guest', 'lynch']

n = 4 

4 words that cover 20 alphabets - ['stock', 'viral', 'debug', 'nymph'] or ['thump', 'candy', 'globe', 'frisk'] or ['blimp', 'retch', 'sound', 'gawky']

n = 5

5 words that cover 23 alphabets - ['block', 'wight', 'vixen', 'safer', 'dumpy'] or ['brave', 'swamp', 'dying', 'quoth', 'flack'] or ['unwed', 'bravo', 'fritz', 'glyph', 'smack']

## Solution Approach
Using Linear Programming, set up the following model:

Variables: 
 - assigned_l for every letter (26 alphabets)
 - assigned_w for every word (2317 5-letter-words in Wordle Dictionary)

Objective Function: 
 - Maximize sum( weight_l * assigned_l )
 where weight_l is the ranking of letter frequency being used in words in the English Dictionary

Constraints: 
 1. For every word (w): 	sum( assigned_l [letters contained in w] ) >= 5 * assigned_w
 2. For every letter (l): 	sum( assigned_w [words containing l] ) >= assigned_l
 3. Single constraint: 		sum( assigned_w ) <= n
 

Example: See "Linear Programming.xlsx" for illustration of letter Weights and Model Constraints