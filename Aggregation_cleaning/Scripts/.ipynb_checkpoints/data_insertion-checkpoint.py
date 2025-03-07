import pandas as pd
import ast
import mysql.connector
import pymongo
from mysql.connector import Error
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load .env file to environment
load_dotenv()

# Access MySQL credentials
SQL_USERNAME = os.getenv('SQL_USERNAME')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')
SQL_HOST = os.getenv('SQL_HOST')
DB_NAME = 'pokemon_project_db'

# Access MongoDB credentials
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')
MONGODB_CLUSTER = os.getenv('MONGODB_CLUSTER')
MONGODB_HOST = os.getenv('MONGODB_HOST')

# MongoDB connection setup
client = MongoClient(f'mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}?retryWrites=true&w=majority&appName={MONGODB_CLUSTER}')

# Select MongoDB database and collections
db = client["pokemon_project_db"]
image_collection = db["Image URL"]
description_collection = db["Descriptions"]

# Connect to MySQL database
def connect_db():
    try:
        conn = mysql.connector.connect(
            host=SQL_HOST,
            database=DB_NAME,
            user=SQL_USERNAME,
            password=SQL_PASSWORD
        )
        return conn
    except Error as e:
        print("Error connecting to MySQL", e)
        exit()

# Establish MySQL connection
conn = connect_db()
cursor = conn.cursor()

# Load CSV file
csv_file_path = "C:\\Users\\Utilisateur\\Pokemon bloc one project\\Create_DB\\prepared_poke_data.csv"
df_poke_data = pd.read_csv(csv_file_path)

# Insert Pokémon data into MySQL
for index, row in df_poke_data.iterrows():
    pokemon_name = row['Pokémon Name']
    pokedex = row['Pokédex Number']
    height, weight = 0, 0  # Default values
    cursor.execute("""
        INSERT INTO Pokemon (name, height, weight, pokedex)
        VALUES (%s, %s, %s, %s)
    """, (pokemon_name, height, weight, pokedex))
conn.commit()

def generate_insert_statements(csv_file):
    pokemon_data = pd.read_csv(csv_file)
    pokemon_data['Pokédex Number'] = pokemon_data['Pokédex Number'].astype(int)
    pokemon_data['Types'] = pokemon_data['Types'].apply(ast.literal_eval)
    pokemon_data['Abilities'] = pokemon_data['Abilities'].apply(ast.literal_eval)
    pokemon_data['Moves'] = pokemon_data['Moves'].apply(ast.literal_eval)
    
    pokemon_types_inserts, pokemon_abilities_inserts, pokemon_moves_inserts = [], [], []
    
    for _, row in pokemon_data.iterrows():
        pokemon_id = row['Pokédex Number']
        for poke_type in row['Types']:
            pokemon_types_inserts.append(
                f"INSERT IGNORE INTO Pokemon_Types (pokemon_id, type_id) VALUES ({pokemon_id}, (SELECT type_id FROM Types WHERE type_name = '{poke_type.replace("'", "''") }'));"
            )
        for ability in row['Abilities']:
            pokemon_abilities_inserts.append(
                f"INSERT IGNORE INTO Pokemon_Abilities (pokemon_id, ability_id) VALUES ({pokemon_id}, (SELECT ability_id FROM Abilities WHERE ability_name = '{ability.replace("'", "''")}'));"
            )
        for move in row['Moves']:
            pokemon_moves_inserts.append(
                f"INSERT IGNORE INTO Pokemon_Moves (pokemon_id, move_id) VALUES ({pokemon_id}, (SELECT move_id FROM Moves WHERE move_name = '{move.replace("'", "''")}'));"
            )
    
    return pokemon_types_inserts, pokemon_abilities_inserts, pokemon_moves_inserts

pokemon_types, pokemon_abilities, pokemon_moves = generate_insert_statements(csv_file_path)

# Execute SQL statements
try:
    for query in pokemon_types + pokemon_abilities + pokemon_moves:
        cursor.execute(query)
    conn.commit()
except Error as e:
    print("Error executing SQL statements", e)
    conn.rollback()
finally:
    cursor.close()
    conn.close()

# Prepare and insert data into MongoDB
image_data = df_poke_data[["Pokédex Number", "Image URL"]].rename(columns={"Pokédex Number": "Pokedex_Number"}).to_dict(orient="records")
description_data = df_poke_data[["Pokédex Number", "Description"]].rename(columns={"Pokédex Number": "Pokedex_Number"}).to_dict(orient="records")

if image_data:
    image_collection.insert_many(image_data)
if description_data:
    description_collection.insert_many(description_data)

print("Data inserted successfully into both MySQL and MongoDB!")
