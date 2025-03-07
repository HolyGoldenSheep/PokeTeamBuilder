import requests
from bs4 import BeautifulSoup
import pandas as pd
import csv

# Scrap Pokémon data from Wikipedia generation pages
def scrape_generation_data(url):
    """
    Scrapes Pokémon generation data from a given URL.
    
    This function fetches an HTML page, parses a sortable wikitable,
    and extracts Pokémon names and their descriptions from the table.
    
    Parameters:
    url (str): The URL of the webpage containing the Pokémon generation data.
    
    Returns:
    list: A list of lists, where each inner list contains the Pokémon name (str)
          and its description (str). Returns an empty list if the request fails
          or the expected table is not found.
    """
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

all_pokemon_data = []
for url in generation_urls:
    all_pokemon_data.extend(scrape_generation_data(url))

if all_pokemon_data:
    df = pd.DataFrame(all_pokemon_data, columns=['Pokemon', 'Description'])
    df.to_csv('all_pokemon_notes.csv', index=False)
    print("Saved generation Pokémon data to 'all_pokemon_notes.csv'")
else:
    print("No Pokémon data found from Wikipedia.")

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
