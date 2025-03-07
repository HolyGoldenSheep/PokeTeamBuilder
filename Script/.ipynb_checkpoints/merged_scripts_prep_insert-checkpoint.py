import os
import ast
import pandas as pd
import mysql.connector
from mysql.connector import Error
from pymongo import MongoClient
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Access MySQL credentials
SQL_USERNAME = os.getenv('SQL_USERNAME')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')
SQL_HOST = os.getenv('SQL_HOST')

# Access MongoDB credentials
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')
MONGODB_CLUSTER = os.getenv('MONGODB_CLUSTER')
MONGODB_HOST = os.getenv('MONGODB_HOST')

# Load CSV files
df_desc = pd.read_csv("all_pokemon_notes.csv")
df_api = pd.read_csv("all_pokemon_info.csv")
df_webscrap = pd.read_csv("pokemon_data_with_images.csv")

# Merge relevant columns
df1 = df_webscrap[['Pokédex Number', 'Pokémon Name', 'Types', 'Image URL']]
df2 = df_api[['Abilities', 'Moves']]
df3 = df_desc[['Description']]
final_df = pd.concat([df1, df2, df3], axis=1).reset_index(drop=True)

# Remove duplicates
final_df = final_df.drop_duplicates()

# Process list columns
def split_and_store(df, columns):
    """
    Splits values in specified columns of a DataFrame and extracts unique values.
    
    This function modifies the given DataFrame by splitting string values in the specified
    columns using ', ' as the delimiter. It also collects unique values from these columns.
    
    Parameters:
    df (pandas.DataFrame): The DataFrame containing the data.
    columns (list of str): A list of column names whose values should be split.
    
    Returns:
    tuple:
        - pandas.DataFrame: The modified DataFrame with split values.
        - dict: A dictionary where keys are column names and values are lists of unique values.
    """
    unique_values = {col: set() for col in columns}
    for col in columns:
        df[col] = df[col].apply(lambda x: x.split(', ') if isinstance(x, str) else [])
        unique_values[col].update([item for sublist in df[col] for item in sublist])
    return df, {col: list(values) for col, values in unique_values.items()}

final_df, unique_values = split_and_store(final_df, ['Types', 'Abilities', 'Moves'])

# Connect to MySQL
def connect_mysql():
    """
    Establishes a connection to the MySQL database.
    
    This function attempts to connect to the MySQL database using predefined
    credentials and returns the connection object if successful.
    
    Returns:
    mysql.connector.connection.MySQLConnection: A MySQL connection object if the
        connection is successful.
    None: If the connection attempt fails, None is returned and an error message
        is printed.
    """
    try:
        conn = mysql.connector.connect(
            host=SQL_HOST,
            database='pokemon_project_db',
            user=SQL_USERNAME,
            password=SQL_PASSWORD
        )
        return conn
    except Error as e:
        print("MySQL Connection Error:", e)
        return None

conn = connect_mysql()
cursor = conn.cursor()

# Insert unique types, abilities, and moves
def insert_unique_values(table, column, values):
    for value in values:
        cursor.execute(f"INSERT IGNORE INTO {table} ({column}) VALUES (%s)", (value,))
    conn.commit()

insert_unique_values("Types", "type_name", unique_values['Types'])
insert_unique_values("Abilities", "ability_name", unique_values['Abilities'])
insert_unique_values("Moves", "move_name", unique_values['Moves'])

# Fetch type, ability, and move IDs
cursor.execute("SELECT type_id, type_name FROM Types")
type_dict = dict(cursor.fetchall())
cursor.execute("SELECT ability_id, ability_name FROM Abilities")
ability_dict = dict(cursor.fetchall())
cursor.execute("SELECT move_id, move_name FROM Moves")
move_dict = dict(cursor.fetchall())

# Insert Pokémon data
for _, row in final_df.iterrows():
    cursor.execute("SELECT id FROM Pokemon WHERE pokedex = %s", (row['Pokédex Number'],))
    existing_pokemon = cursor.fetchone()
    
    if not existing_pokemon:
        cursor.execute("INSERT INTO Pokemon (name, height, weight, pokedex) VALUES (%s, %s, %s, %s)",
                       (row['Pokémon Name'], 0, 0, row['Pokédex Number']))
        pokemon_id = cursor.lastrowid
    else:
        pokemon_id = existing_pokemon[0]
    
    for poke_type in row['Types']:
        cursor.execute("INSERT IGNORE INTO Pokemon_Types (pokemon_id, type_id) VALUES (%s, %s)",
                       (pokemon_id, type_dict.get(poke_type)))
    
    for ability in row['Abilities']:
        cursor.execute("INSERT IGNORE INTO Pokemon_Abilities (pokemon_id, ability_id) VALUES (%s, %s)",
                       (pokemon_id, ability_dict.get(ability)))
    
    for move in row['Moves']:
        cursor.execute("INSERT IGNORE INTO Pokemon_Moves (pokemon_id, move_id) VALUES (%s, %s)",
                       (pokemon_id, move_dict.get(move)))

conn.commit()
cursor.close()
conn.close()

# Insert data into MongoDB
client = MongoClient(f'mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}?retryWrites=true&w=majority&appName={MONGODB_CLUSTER}')
db = client["pokemon_project_db"]
image_collection = db["Image URL"]
description_collection = db["Descriptions"]

image_data = final_df[['Pokédex Number', 'Image URL']].rename(columns={"Pokédex Number": "Pokedex_Number"}).to_dict(orient="records")
description_data = final_df[['Pokédex Number', 'Description']].rename(columns={"Pokédex Number": "Pokedex_Number"}).to_dict(orient="records")

if image_data:
    for img in image_data:
        if not image_collection.find_one({"Pokedex_Number": img["Pokedex_Number"]}):
            image_collection.insert_one(img)

if description_data:
    for desc in description_data:
        if not description_collection.find_one({"Pokedex_Number": desc["Pokedex_Number"]}):
            description_collection.insert_one(desc)

print("Data inserted successfully!")

