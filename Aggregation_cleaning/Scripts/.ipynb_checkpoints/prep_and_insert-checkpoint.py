import requests
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
import pandas as pd

#Load csv files
df_webscrap_description = pd.read_csv("all_pokemon_notes.csv")
df_public_api = pd.read_csv("all_pokemon_info.csv")
df_webscrap = pd.read_csv("pokemon_data_with_images.csv")

# Select specific columns from each DataFrame
df1_selected = df_webscrap[['Pokédex Number', 'Pokémon Name', 'Types', 'Image URL']]
df2_selected = df_public_api[['Abilities', 'Moves']]
df3_selected = df_webscrap_description[['Description']]

# Concatenate the selected columns horizontally
final_df = pd.concat([df1_selected, df2_selected, df3_selected], axis=1)
final_df = final_df.reset_index(drop=True)

#prepare data again
def apply_split_to_columns(df, columns):
    all_values = {column: [] for column in columns}
    unique_values = {column: [] for column in columns} 
    
    # Iterate over the specified columns and split the values
    for column in columns:
        for cell in df[column].map(lambda x: x.split(', ')):
            all_values[column] += cell
        
        # Update the dataframe with the split values
        df[column] = df[column].map(lambda x: x.split(', '))
        
        # Store the unique values for the column
        unique_values[column] = list(set(all_values[column]))  # Remove duplicates 
    
    return df, all_values, unique_values

# Apply to the dataframe
columns_to_split = ['Types', 'Abilities', 'Moves']
final_df, all_values, unique_values = apply_split_to_columns(final_df, columns_to_split)

# Print the unique values for each column
print("Unique Types:", unique_values['Types'])
print("Unique Abilities:", unique_values['Abilities'])
print("Unique Moves:", unique_values['Moves'])

# Load .env file to environment
load_dotenv()

# Access the MongoDB username and password
SQL_USERNAME = os.getenv('SQL_USERNAME')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')
SQL_HOST =  os.getenv('SQL_HOST')
# Connect to the MySQL database
conn = mysql.connector.connect(
            host=f'{SQL_HOST}',
            database='pokemon_project_db',
            user=f'{SQL_USERNAME}',
            password=f'{SQL_PASSWORD}'
        )
cursor = conn.cursor()

# Insert unique types into the Types table
for type_name in unique_values['Types']:
    cursor.execute("INSERT INTO Types (type_name) VALUES (%s)", (type_name,))

# Commit the transaction
conn.commit()

# Fetching their type_ids
cursor.execute("SELECT type_id, type_name FROM Types")
types = cursor.fetchall()
type_dict = {type_name: type_id for type_id, type_name in types}

# Insert unique abilities into the Abilities table
for ability_name in unique_values['Abilities']:
    cursor.execute("INSERT INTO Abilities (ability_name) VALUES (%s)", (ability_name,))

# Commit the transaction
conn.commit()

# Fetch the ability_ids
cursor.execute("SELECT ability_id, ability_name FROM Abilities")
abilities = cursor.fetchall()
ability_dict = {ability_name: ability_id for ability_id, ability_name in abilities}

# Insert unique moves into the Moves table
for move_name in unique_values['Moves']:
    cursor.execute("INSERT INTO Moves (move_name) VALUES (%s)", (move_name,))

# Commit the transaction
conn.commit()

# fetch their move_ids
cursor.execute("SELECT move_id, move_name FROM Moves")
moves = cursor.fetchall()
move_dict = {move_name: move_id for move_id, move_name in moves}

#Insert the pokemon and the pokedex number 
for index, row in final_df.iterrows():
    pokemon_name = row['Pokémon Name']
    pokedex = row['Pokédex Number']

    # Set default values for height and weight since we don't have data for them
    height = 0  # or 0 if you want a default value
    weight = 0  # or 0 if you want a default value

    # Inserting Pokémon name and Pokedex number into the Pokemon table
    cursor.execute("""
        INSERT INTO Pokemon (name, height, weight, pokedex)
        VALUES (%s, %s, %s, %s)
    """, (pokemon_name, height, weight, pokedex))

# Commit the final changes
conn.commit()

# Close the cursor and connection
cursor.close()
conn.close()


#INSERTING DATA TO MONGODB

import pymongo
import pandas as pd 
from pymongo import MongoClient
from dotenv import load_dotenv
import os 
# Load .env file to environment
load_dotenv()

# Access the MongoDB username and password
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')
MONGODB_CLUSTER = os.getenv('MONGODB_CLUSTER')
MONGODB_HOST =  os.getenv('MONGODB_HOST')

# MongoDB connection setup
client = MongoClient(f'mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}?retryWrites=true&w=majority&appName={MONGODB_CLUSTER}')

# Select database and collections
db = client["pokemon_project_db"]
image_collection = db["Image URL"]
description_collection = db["Descriptions"]

# Load the CSV file
file_path = "C:\\Users\\Utilisateur\\Pokemon bloc one project\\Create_DB\\prepared_poke_data.csv"  
df = pd.read_csv(file_path)


# Prepare Image URL data
image_data = df[["Pokédex Number", "Image URL"]].rename(columns={"Pokédex Number": "Pokedex_Number"}).to_dict(orient="records")

# Prepare Description data
description_data = df[["Pokédex Number", "Description"]].rename(columns={"Pokédex Number": "Pokedex_Number"}).to_dict(orient="records")

# Insert data into MongoDB collections
if image_data:
    image_collection.insert_many(image_data)
if description_data:
    description_collection.insert_many(description_data)

print("Data inserted successfully!")