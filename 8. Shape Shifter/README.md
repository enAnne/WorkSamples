# Shape Shifter
Putting together a few little things I picked up over the years, through guidance or self-exploration:<br />
Primary School - Solving Neopets ShapeShifter game manually <br />
High School - Even/Odd numbers, Algebra, Modulus<br />
Monash University - Matrix operations with Matlab<br />
1st job at Quintiq - Optimization / Linear Programming with Quill<br />
2nd job at 2X Marketing - Data manipulation with Python<br />
3rd job at Mercedes - Browser automation & Web scraping with Selenium library<br />
4th job at Mastercard - Linear Programming with Gekko library and SimpleGUI library<br />
5th job at Cognizant - That anyone can learn anything with an open mind, Google, and grit.<br />

Solving my favourite childhood puzzle using Python Gekko (linear programming) and Selenium (web automation).
 
## Challenge
In Wordle, you have 6 tries to guess the correct word. In Absurdle - unlimited.<br />
The first few tries is where you uncover the letters that form the correct word.<br />
The last try is just a permutation of those letters.

Ideally, you'd want to uncover all the correct letters in as few tries as possible.<br />
So what are the best words to spend the first ***n*** tries on?

## Solution
***n = 3*** &nbsp;&nbsp; *(3 words that cover 15 most frequent alphabets)*
 - ['pithy', 'could', 'snare'] 
 - ['itchy', 'paler', 'sound'] 
 - ['crust', 'daily', 'phone']  
 - ['radio', 'guest', 'lynch'] 
 - ...

***n = 4*** &nbsp;&nbsp; *(4 words that cover 20 most frequent alphabets)*
 - ['stock', 'viral', 'debug', 'nymph'] 
 - ['thump', 'candy', 'globe', 'frisk'] 
 - ['blimp', 'retch', 'sound', 'gawky'] 
 - ...

***n = 5*** &nbsp;&nbsp; *(5 words that cover 24 most frequent alphabets)*
 - ['dwarf', 'black', 'ghost', 'vixen', 'jumpy']
 
***n = 6*** &nbsp;&nbsp; *(6 words that cover all alphabets)*
 - ['fjord', 'gawky', 'waltz', 'chump', 'vixen', 'squib']

## Solution Approach
Using Linear Programming, set up a simple assignment model:

**Variables:**
 - assigned_l - for every letter (26 alphabets)
 - assigned_w - for every word (2317 five-letter-words in Wordle Dictionary)

**Objective Function:**
 - Maximize sum( weight_l * assigned_l )
 where weight_l is the ranking of letter frequency being used in words in the English Dictionary

**Constraints:**
 1. For every word (w): &nbsp;&nbsp;&nbsp;&nbsp; sum( assigned_l [letters contained in w] ) >= 5 * assigned_w
 2. For every letter (l): &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; sum( assigned_w [words containing l] ) >= assigned_l
 3. Single constraint: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  sum( assigned_w ) <= n
 

Example: See "Linear Programming.xlsx" for illustration of letter Weights and Model Constraints
