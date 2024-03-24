
# Chao Fan

Generate meal plans automatically using what's out there on the internet.

- [x] Create pecipe database generation pipeline
- [ ] Create meal plan pipeline
- [x] Setup pipelines to run automatically in cloud - use GitHub actions
- [ ] Create web app for choosing meal plans
- [ ] Create walmart order pipeline

## Pipelines

### Recipe database generation
1. Pull recipe pins from Cookin' pinterest board
2. Check if there are any new pins (i.e., ones not in the database)
2. Extract structured version of new recipes using spoonacular
3. Put the structured versions in the database

### Meal plan generation
1. Generate themes
2. Search in recipe database for recipes similar to that them
    a.  Possibly augment that database by searching on spoonacular
3. Generate a list of all possible meals with those recipes and score them
4. Choose the top meal plans to show the user

### Walmart order
1. Create grocery list from meal plan
2. Use LaVague model to traverese walmart.com and place order

## Setup

0. Clone the repository: `git clone https://github.com/marcosfelt/chao_fan.git`
1. Install the dependencies: `poetry install` or `pip install -e .`
2. Download [postgres.app](https://postgresapp.com/downloads.html) and install the [CLI tools](https://postgresapp.com/documentation/cli-tools.html)
3. Run `createdb chao_fan`
4. Open the PostgreSQL repl (`psql chao_fan`) and run the following command: `CREATE EXTENSION vector;`
5. Create the tables in the db by running `setup_db`.