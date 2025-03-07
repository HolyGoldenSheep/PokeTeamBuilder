import requests
from bs4 import BeautifulSoup
import pandas as pd

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

# List to store all Pokémon data
all_pokemon_data = []

# Function to scrape Pokémon data from a single generation URL
def scrape_generation_data(url):
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code != 200:
        print(f"Failed to retrieve the page: {url}. Status code:", response.status_code)
        return []

    # Parse the content of the response using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Try to find the table with Pokémon descriptions
    table = soup.select_one('table.wikitable.sortable')

    # Check if the table is found
    if table is None:
        print(f"Table not found for URL: {url}. Please check the HTML structure.")
        return []

    generation_pokemon_data = []

    # Iterate through the rows of the table
    for row in table.find_all('tr')[1:]:  # Skip the header row
        # Get the Pokémon name (from the <th> tag inside the <tr> with a specific id)
        name_tag = row.find('th')
        if name_tag:
            name = name_tag.get_text(strip=True)  # Pokémon name in the <th> tag
        else:
            name = "Unknown"

        # Get the description (usually the last <td> tag in the row)
        description_td = row.find_all('td')[-1]  # Get the last <td> tag
        if description_td:
            description = description_td.get_text(strip=True)
            generation_pokemon_data.append([name, description])
    
    return generation_pokemon_data

# Iterate through each generation URL and scrape data
for url in generation_urls:
    generation_data = scrape_generation_data(url)
    
    # Append the data to the all_pokemon_data list
    if generation_data:
        all_pokemon_data.extend(generation_data)

# Check if any data was collected
if not all_pokemon_data:
    print("No Pokémon data was found.")
else:
    # Create a pandas DataFrame from the collected data
    df = pd.DataFrame(all_pokemon_data, columns=['Pokemon', 'Description'])

    # Save to a CSV file
    df.to_csv('all_pokemon_notes.csv', index=False)
    print("Scraping completed and data saved to 'all_pokemon_notes.csv'.")
