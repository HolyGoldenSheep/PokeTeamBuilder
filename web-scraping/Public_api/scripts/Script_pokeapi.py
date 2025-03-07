import requests
import csv

# Function to fetch the list of all Pokémon names
def get_all_pokemon_names():
    """
    Fetches the names of all available Pokémon from the PokeAPI.

    This function sends requests to the PokeAPI to retrieve the names of Pokémon. It handles pagination to fetch
    all Pokémon names up to the limit of 1025 Pokémon.

    Returns:
        list: A list of Pokémon names (strings).
    """
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

# Function to fetch abilities and moves for a specific Pokémon
def get_pokemon_info(pokemon_name):
    """
    Fetches the abilities and moves for a specific Pokémon.

    This function sends a request to the PokeAPI to retrieve detailed information about a Pokémon's abilities and moves.

    Args:
        pokemon_name (str): The name of the Pokémon whose data is to be retrieved.

    Returns:
        dict: A dictionary containing 'abilities' and 'moves' lists, or None if the Pokémon data could not be fetched.
    """
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
    """
    Retrieves Pokémon data and saves it to a CSV file.

    This function fetches the names, abilities, and moves of all Pokémon and writes this data into a CSV file
    called 'all_pokemon_info.csv'. Each row in the CSV file corresponds to one Pokémon and its abilities and moves.

    Returns:
        None
    """
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
if __name__ == "__main__":
    save_all_to_csv()
