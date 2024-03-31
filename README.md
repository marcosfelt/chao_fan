
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

## Local Setup

0. Clone the repository: `git clone https://github.com/marcosfelt/chao_fan.git`
1. Install the dependencies: `poetry install` or `pip install -e .`
2. Download [postgres.app](https://postgresapp.com/downloads.html) and install the [CLI tools](https://postgresapp.com/documentation/cli-tools.html)
3. Run `createdb chao_fan`
4. Open the PostgreSQL repl (`psql chao_fan`) and run the following command: `CREATE EXTENSION vector;`
5. Create the tables in the db by running `setup_db`.
6. Create a `.env` file filling in the missing variable avlues below:
    ```bash
    PINTEREST_EMAIL=
    PINTEREST_PASSWORD=
    PINTEREST_USERNAME=
    PINTEREST_BOARD_NAME="Cookin'"
    SPOONACULAR_API_KEY=
    OPENAI_API_KEY=
    EMBEDDING_DIMENSION=384
    INGREDIENT_EMBEDDING_GENERATION_BATCH_SIZE=10000
    INGREDIENT_EMBEDDING_GENERATION_TIMEOUT_SECONDS=600
    POSTGRES_URL=postgresql://localhost/chao_fan
    OVERWRITE_TABLES=False
    ```
6. Download the nutrition SQLite database from [here](https://drive.google.com/open?id=15Q32X2XQ9FRMcwIkKHS1SMvCZUQIA-ah&usp=drive_fs) and place in a directory called `data` in the repository.
7. Insert the nutrition and price data into the database:
    ```bash
    python scripts/insert_ingredient_nutrition.py data/CompFood.sqlite
    python scripts/insert_ingredient_prices.py
    ```

## Render

**Database**
0. Setup a Postgres Database
1. Coy the **external** url and paste locally in your `.env`. Run `setup_db` to create the tables.
2. Copy the **internal** database url. Replace `postgres` with `postgresql`

**Update recipe cron job**
1. Create a cron job to run `chao_fan/pipelines/update_recipe_db.py`
2. Paste the .env file from step 6 above in the environments tab.  Use the link from step 2 in database `POSTGRES_URL`.