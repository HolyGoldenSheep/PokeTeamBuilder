import requests
from bs4 import BeautifulSoup
import pandas as pd
import csv
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
import pymongo
from pymongo import MongoClient

# Load .env file to environment
load_dotenv()

# Database credentials for MySQL and MongoDB
SQL_USERNAME = os.getenv('SQL_USERNAME')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')
SQL_HOST = os.getenv('SQL_HOST')
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')
MONGODB_CLUSTER = os.getenv('MONGODB_CLUSTER')
MONGODB_HOST = os.getenv('MONGODB_HOST')

# Scrap Pokémon data from Wikipedia generation pages
def scrape_generation_data(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve {url}. Status code: {response.status_code}")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.select_one('table.wikitable.sortable')
    if table is None:
        print(f"Table not found for {url}")
        return []
    
    generation_pokemon_data = []
    for row in table.find_all('tr')[1:]:
        name_tag = row.find('th')
        name = name_tag.get_text(strip=True) if name_tag else "Unknown"
        
        description_td = row.find_all('td')[-1]
        description = description_td.get_text(strip=True) if description_td else "No description"
        
        generation_pokemon_data.append([name, description])
    
    return generation_pokemon_data

# List of generation URLs to scrape
generation_urls = [
    "https://en.wikipedia.org/wiki/List_of_generation_I_Pokémon",
    "https://en.wikipedia.org/wiki/List_of_generation_II_Pokémon",
    "https://en.wikipedia.org/wiki/List_of_generation_III_Pokémon",
    "https://en.wikipedia.org/wiki/List_of_generation_IV_Pokémon",
    "https://en.wikipedia.org/wiki/List_of_generation_V_Pokémon",
    "https://en.wikipedia.org/wiki/List_of_generation_VI_Pokémon",
    "https://en.wikipedia.org/wiki/List_of_generation_VII_Pokémon",
    "https://en.wikipedia.org/wiki/List_of_generation_VIII_Pokémon",
    "https://en.wikipedia.org/wiki/List_of_generation_IX_Pokémon"
]

# Scraping Pokémon data from Wikipedia
all_pokemon_data = []
for url in generation_urls:
    all_pokemon_data.extend(scrape_generation_data(url))

# Save Pokémon data to CSV
if all_pokemon_data:
    df_webscrap_description = pd.DataFrame(all_pokemon_data, columns=['Pokemon', 'Description'])
    df_webscrap_description.to_csv('all_pokemon_notes.csv', index=False)
    print("Saved generation Pokémon data to 'all_pokemon_notes.csv'")

# Scrape Pokémon data with images from Pokémon Database
url = "https://pokemondb.net/pokedex/national"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

with open('pokemon_data_with_images.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Pokédex Number', 'Pokémon Name', 'Types', 'Image URL'])
    
    infocards = soup.find_all('div', class_='infocard')
    for card in infocards:
        pokedex_number = card.find('small').text.strip().replace('#', '')
        pokemon_name = card.find('a', class_='ent-name').text.strip()
        types = [type_span.text.strip() for type_span in card.find_all('a', class_='itype')]
        img_url = card.find('img', class_='img-fixed')['src']
        writer.writerow([pokedex_number, pokemon_name, ', '.join(types), img_url])

print("Saved National Pokédex data to 'pokemon_data_with_images.csv'")

# Function to fetch the list of all Pokémon names from the PokeAPI
def get_all_pokemon_names():
    pokemon_names = []
    url = "https://pokeapi.co/api/v2/pokemon?limit=1025"  # Limit to 1025 Pokémon
    while url:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            pokemon_names.extend([pokemon["name"] for pokemon in data["results"]])
            url = data["next"]  # Get the next page 
        else:
            print("Error fetching Pokémon list.")
            break
    return pokemon_names

# Function to fetch abilities and moves for a specific Pokémon from PokeAPI
def get_pokemon_info(pokemon_name):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
    response = requests.get(url)
    
    if response.status_code == 200:
        pokemon_data = response.json()
        pokemon_info = {
            "abilities": [ability["ability"]["name"] for ability in pokemon_data["abilities"]],
            "moves": [move_data["move"]["name"] for move_data in pokemon_data["moves"]]
        }
        return pokemon_info
    else:
        return None

# Function to save the Pokémon info into a single CSV file
def save_all_to_csv():
    pokemon_names = get_all_pokemon_names()
    
    # Define the header for the CSV file
    header = ["Pokemon Name", "Abilities", "Moves"]
    
    # Open the CSV file to write the data
    with open("all_pokemon_info.csv", mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        
        # Loop through all Pokémon and fetch their data
        for pokemon_name in pokemon_names:
            pokemon_info = get_pokemon_info(pokemon_name)
            
            if pokemon_info:
                abilities = ', '.join(pokemon_info["abilities"])
                moves = ', '.join(pokemon_info["moves"])
                writer.writerow([pokemon_name, abilities, moves])
                print(f"Data for {pokemon_name} saved.")
            else:
                print(f"Could not retrieve data for {pokemon_name}.")
                
    print("All Pokémon data saved to all_pokemon_info.csv.")

# Run the function to save all Pokémon data into one CSV file
save_all_to_csv()

# Load CSV files
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

# Prepare data for insertion into MySQL
def apply_split_to_columns(df, columns):
    all_values = {column: [] for column in columns}
    unique_values = {column: [] for column in columns} 
    
    for column in columns:
        for cell in df[column].map(lambda x: x.split(', ')):
            all_values[column] += cell
        
        df[column] = df[column].map(lambda x: x.split(', '))
        
        unique_values[column] = list(set(all_values[column]))  # Remove duplicates 
    
    return df, all_values, unique_values

columns_to_split = ['Types', 'Abilities', 'Moves']
final_df, all_values, unique_values = apply_split_to_columns(final_df, columns_to_split)

# Connect to MySQL database
conn = mysql.connector.connect(
    host=SQL_HOST,
    database='pokemon_project_db',
    user=SQL_USERNAME,
    password=SQL_PASSWORD
)
cursor = conn.cursor()

# Insert unique types into the Types table
for type_name in unique_values['Types']:
    cursor.execute("INSERT INTO Types (type_name) VALUES (%s)", (type_name,))

# Commit the transaction
conn.commit()

# Fetch the type_ids
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

# Fetch their move_ids
cursor.execute("SELECT move_id, move_name FROM Moves")
moves = cursor.fetchall()
move_dict = {move_name: move_id for move_id, move_name in moves}

# Insert Pokémon into the Pokemon table
for index, row in final_df.iterrows():
    pokemon_name = row['Pokémon Name']
    pokedex = row['Pokédex Number']

    # Set default values for height and weight
    height = 0  # Default
    weight = 0  # Default

    cursor.execute("""
        INSERT INTO Pokemon (name, height, weight, pokedex)
        VALUES (%s, %s, %s, %s)
    """, (pokemon_name, height, weight, pokedex))

# Commit the final changes
conn.commit()

# Close the cursor and connection
cursor.close()
conn.close()

# MongoDB insertion
client = MongoClient(f'mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}?retryWrites=true&w=majority&appName={MONGODB_CLUSTER}')
db = client["pokemon_project_db"]
image_collection = db["Image URL"]
description_collection = db["Descriptions"]

# Prepare and insert data into MongoDB
image_data = final_df[["Pokédex Number", "Image URL"]].rename(columns={"Pokédex Number": "Pokedex_Number"}).to_dict(orient="records")
description_data = final_df[["Pokédex Number", "Description"]].rename(columns={"Pokédex Number": "Pokedex_Number"}).to_dict(orient="records")

if image_data:
    image_collection.insert_many(image_data)
if description_data:
    description_collection.insert_many(description_data)

print("Data inserted into MongoDB successfully!")
