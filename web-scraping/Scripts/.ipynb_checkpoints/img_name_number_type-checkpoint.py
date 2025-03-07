import requests
from bs4 import BeautifulSoup
import csv

# URL of the National Pokémon Pokedex page
url = "https://pokemondb.net/pokedex/national"

# Send a GET request to fetch the page content
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Open CSV file for writing
with open('pokemon_data_with_images.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    
    # Write the header row
    writer.writerow(['Pokédex Number', 'Pokémon Name', 'Types', 'Image URL'])
    
    # Find all Pokémon info divs
    infocards = soup.find_all('div', class_='infocard')
    
    # Loop through each infocard and extract relevant details
    for card in infocards:
        # Extract Pokédex number
        pokedex_number = card.find('small').text.strip().replace('#', '')
        
        # Extract Pokémon name
        pokemon_name = card.find('a', class_='ent-name').text.strip()
        
        # Extract Pokémon types
        types = [type_span.text.strip() for type_span in card.find_all('a', class_='itype')]
        
        # Extract Pokémon image URL
        img_url = card.find('img', class_='img-fixed')['src']
        
        # Write the data to the CSV
        writer.writerow([pokedex_number, pokemon_name, ', '.join(types), img_url])

print("Scraping completed and data saved to pokemon_data_with_images.csv")
