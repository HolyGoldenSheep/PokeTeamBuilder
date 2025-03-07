import os
import jwt
import datetime
from fastapi import FastAPI, Query, Depends, HTTPException, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import mysql.connector as connector
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient
from fastapi.responses import HTMLResponse

# Load the .env file
load_dotenv(override=True)

# Access MongoDB credentials
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')
MONGODB_CLUSTER = os.getenv('MONGODB_CLUSTER')
MONGODB_HOST = os.getenv('MONGODB_HOST')

# Access SQL credentials
SQL_USERNAME = os.getenv('SQL_USERNAME')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')
SQL_HOST = os.getenv('SQL_HOST')

# Token settings
SECRET_KEY = os.getenv("SECRET_KEY")
API_PASSWORD = os.getenv("API_PASSWORD")

# Initialize FastAPI app
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# MongoDB connection setup
client = MongoClient(f'mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}?retryWrites=true&w=majority&appName={MONGODB_CLUSTER}')
db = client["pokemon_project_db"]
image_collection = db["Image URL"]
description_collection = db["Descriptions"]



#Configure security for Bearer tokens
security = HTTPBearer()

# TokenRequest model for token generation
class TokenRequest(BaseModel):
    password: str
    duration: Optional[int] = 3600  # 1 hour 

# Generate JWT token with an expiration
def create_jwt(duration: int) -> str:
    """
    Generates a JSON Web Token (JWT) with an expiration time.

    Args:
        duration (int): Duration in seconds for how long the token should be valid.

    Returns:
        str: The encoded JWT token.
    """
    expiration = datetime.datetime.utcnow() + datetime.timedelta(seconds=duration)
    return jwt.encode(
        {"exp": expiration},
        SECRET_KEY,
        algorithm="HS256"
    )

# Endpoint to generate a JWT token
@app.post("/token")
def generate_token(request: TokenRequest):
    """
    API endpoint to generate a JWT token for a user.

    Args:
        request (TokenRequest): The token request containing the duration and password.

    Raises:
        HTTPException: If the password is incorrect.

    Returns:
        dict: A dictionary containing the JWT token.
    """
    if request.password != API_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid password")
    token = create_jwt(request.duration)
    return {"token": token}

# Function to verify the JWT token
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verifies the validity of the JWT token provided by the user.

    Args:
        credentials (HTTPAuthorizationCredentials): The credentials for the authorization header.

    Raises:
        HTTPException: If the token is expired or invalid.

    Returns:
        None: If the token is valid, it simply passes without returning anything.
    """
    try:
        jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Function to get the MySQL database connection
def get_db_connection():
    """
    Establishes a connection to the MySQL database.

    Raises:
        HTTPException: If there is a database connection error.

    Returns:
        connection: The MySQL database connection object.
    """
    try:
        conn = connector.connect(
            host=SQL_HOST,
            user=SQL_USERNAME,
            password=SQL_PASSWORD,
            database="pokemon_project_db"
        )
        return conn
    except connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database connection error: {err}")

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    """
    Returns the main HTML page of the application.

    Args:
        request (Request): The incoming request to render the page.

    Returns:
        TemplateResponse: The rendered HTML page.
    """
    return templates.TemplateResponse("index.html", {"request": request})

# Get Pokémon by Name 
@app.get("/pokemon", dependencies=[Depends(verify_token)])
def get_pokemon(name: str = Query(..., title="Pokemon Name", description="Enter the Pokémon name")):
    """
    Fetches Pokémon details by name, including types, abilities, moves, description, and image.

    Args:
        name (str): The name of the Pokémon to search for.

    Raises:
        HTTPException: If no Pokémon is found or there are issues fetching data.

    Returns:
        dict: A dictionary containing the Pokémon's details.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)  

    query = """
        SELECT 
            p.pokedex AS pokedex_number, 
            p.name, 
            GROUP_CONCAT(DISTINCT t.type_name) AS type_names,
            GROUP_CONCAT(DISTINCT a.ability_name) AS ability_names,
            GROUP_CONCAT(DISTINCT m.move_name) AS move_names
        FROM pokemon p
        LEFT JOIN pokemon_types pt ON p.pokemon_id = pt.pokemon_id
        LEFT JOIN types t ON pt.type_id = t.type_id
        LEFT JOIN pokemon_abilities pa ON p.pokemon_id = pa.pokemon_id
        LEFT JOIN abilities a ON pa.ability_id = a.ability_id
        LEFT JOIN pokemon_moves pm ON p.pokemon_id = pm.pokemon_id
        LEFT JOIN moves m ON pm.move_id = m.move_id
        WHERE p.name = %s
        GROUP BY p.pokemon_id
    """

    cursor.execute(query, (name,))
    record = cursor.fetchone()
    
    cursor.close()
    conn.close()

    if not record:
        raise HTTPException(status_code=404, detail="Pokémon not found")

    pokedex_number = record["pokedex_number"]

    # Get description from MongoDB
    description_data = description_collection.find_one({"Pokedex_Number": pokedex_number}, {"_id": 0, "Description": 1})
    description = description_data["Description"] if description_data else None

    # Get image URL from MongoDB
    image_data = image_collection.find_one({"Pokedex_Number": pokedex_number}, {"_id": 0, "Image URL": 1})
    image_url = image_data["Image URL"] if image_data else None

    return {
        "pokemon": {
            "name": record["name"],
            "types": record["type_names"].split(",") if record["type_names"] else [],
            "abilities": record["ability_names"].split(",") if record["ability_names"] else [],
            "moves": record["move_names"].split(",") if record["move_names"] else [],
            "pokedex_number": pokedex_number,
            "image": image_url,
            "description": description,
        }
    }

# Get Pokémon by Move 
@app.get("/pokemon/move", dependencies=[Depends(verify_token)])
def get_pokemon_by_move(move_name: str = Query(..., title="Move Name", description="Enter the Move name")):
    """
    Fetches Pokémon that can learn a specific move.

    Args:
        move_name (str): The name of the move to search for.

    Raises:
        HTTPException: If no Pokémon are found that can learn the move.

    Returns:
        dict: A dictionary containing the move and a list of Pokémon that can learn it.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT p.pokedex, p.name 
        FROM pokemon p
        JOIN pokemon_moves pm ON p.pokemon_id = pm.pokemon_id
        JOIN moves m ON pm.move_id = m.move_id
        WHERE m.move_name = %s
        ORDER BY p.pokedex
    """

    cursor.execute(query, (move_name,))
    records = cursor.fetchall()
    
    cursor.close()
    conn.close()

    if not records:
        raise HTTPException(status_code=404, detail=f"No Pokémon found that can learn {move_name}")

    return {"move": move_name, "pokemon": records}

#  Get Pokémon by Type 
@app.get("/pokemon/type", dependencies=[Depends(verify_token)])
def get_pokemon_by_type(type_name: str = Query(..., title="Pokemon Type", description="Enter the Pokémon type")):
    """
    Fetches Pokémon of a specific type.

    Args:
        type_name (str): The type of the Pokémon to search for.

    Raises:
        HTTPException: If no Pokémon of the specified type are found.

    Returns:
        dict: A dictionary containing the type and a list of Pokémon with that type.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT p.pokedex, p.name 
        FROM pokemon p
        JOIN pokemon_types pt ON p.pokemon_id = pt.pokemon_id
        JOIN types t ON pt.type_id = t.type_id
        WHERE t.type_name = %s
        ORDER BY p.pokedex
    """

    cursor.execute(query, (type_name,))
    records = cursor.fetchall()

    cursor.close()
    conn.close()

    if not records:
        raise HTTPException(status_code=404, detail=f"No Pokémon found with type {type_name}")

    return {"type": type_name, "pokemon": records}
# Get pokémon by Ability
@app.get("/pokemon-by-ability", dependencies=[Depends(verify_token)])
def get_pokemon_by_ability(ability_name: str = Query(..., description="Ability name to search for")):
    """
    Fetches Pokémon that have a specific ability.

    Args:
        ability_name (str): The ability to search for.

    Raises:
        HTTPException: If no Pokémon with the specified ability are found.

    Returns:
        dict: A dictionary containing the ability name and a list of Pokémon with that ability.
    """
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)  

    sql_command = """
        SELECT p.pokedex, p.name 
        FROM pokemon p
        JOIN pokemon_abilities pa ON p.pokemon_id = pa.pokemon_id
        JOIN abilities a ON pa.ability_id = a.ability_id
        WHERE a.ability_name = %s
        ORDER BY p.pokedex
    """

    cursor.execute(sql_command, (ability_name,))  
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    if not results:
        raise HTTPException(status_code=404, detail=f"No Pokémon found with the ability '{ability_name}'")

    return {
        "ability_name": ability_name,
        "pokemon": [{"pokedex": record["pokedex"], "name": record["name"]} for record in results]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))