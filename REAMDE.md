

## Meal plan pipeline
1. Generate themes
2. Search in recipe database for recipes similar to that them
    a.  Possibly augment that database by searching on spoonacular
3. Generate a list of all possible meals with those recipes and score them
4. Choose the top meal plans to show the user

## Recipe database generation
1. Pull recipe pins from Cookin' pinterest board
2. Check if there are any new pins (i.e., ones not in the database)
2. Extract structured version of new recipes using spoonacular
3. Put the structured versions in the database

## Walmart order pipeline
1. Create grocery list from meal plan
2. Use LaVague model to traverese walmart.com and place order