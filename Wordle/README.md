# Wordle
The New York Times game - https://www.nytimes.com/games/wordle/index.html

## Challenge
You have 6 tries to guess the correct word.
The first few tries is where you uncover the letters that form the correct word.
The last try is just a permutation of those letters.

Ideally, you'd want to uncover all the correct letters in as few tries as possible.
So what are the best words to spend the first n tries on?

## Solution
**n = 3**  *(3 words that cover 15 most frequent alphabets)*
 - ['pithy', 'could', 'snare'] 
 - ['itchy', 'paler', 'sound'] 
 - ['crust', 'daily', 'phone']  
 - ['radio', 'guest', 'lynch'] 
 - ...

**n = 4**  *(4 words that cover 20 most frequent alphabets)*
 - ['stock', 'viral', 'debug', 'nymph'] 
 - ['thump', 'candy', 'globe', 'frisk'] 
 - ['blimp', 'retch', 'sound', 'gawky'] 
 - ...

**n = 5**  *(5 words that cover 23 most frequent alphabets)*
 - ['block', 'wight', 'vixen', 'safer', 'dumpy'] 
 - ['brave', 'swamp', 'dying', 'quoth', 'flack'] 
 - ['unwed', 'bravo', 'fritz', 'glyph', 'smack'] 
 - ...

## Solution Approach
Using Linear Programming, set up a simple assignment model:

**Variables:**
 - assigned_l - for every letter (26 alphabets)
 - assigned_w - for every word (2317 five-letter-words in Wordle Dictionary)

**Objective Function:**
 - Maximize sum( weight_l * assigned_l )
 where weight_l is the ranking of letter frequency being used in words in the English Dictionary

**Constraints:**
 1. For every word (w): &nbsp&nbsp&nbsp&nbsp sum( assigned_l [letters contained in w] ) >= 5 * assigned_w
 2. For every letter (l): &nbsp&nbsp&nbsp&nbsp sum( assigned_w [words containing l] ) >= assigned_l
 3. Single constraint: &nbsp&nbsp&nbsp&nbsp &nbsp&nbsp&nbsp&nbsp  sum( assigned_w ) <= n
 

Example: See "Linear Programming.xlsx" for illustration of letter Weights and Model Constraints