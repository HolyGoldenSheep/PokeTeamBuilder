from fastapi import FastAPI, Request, Query, Depends, HTTPException, Header
from fastapi.responses import HTMLResponse
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import mysql.connector as connector
from fastapi.templating import Jinja2Templates
import jwt
from pydantic import BaseModel
from typing import Optional
import datetime

# Load environment variables from the .env file
load_dotenv(override=True)

# Access MongoDB credentials from .env
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')
MONGODB_CLUSTER = os.getenv('MONGODB_CLUSTER')
MONGODB_HOST = os.getenv('MONGODB_HOST')

# Access SQL credentials from .env
SQL_USERNAME = os.getenv('SQL_USERNAME')
SQL_PASSWORD = os.getenv('SQL_PASSWORD')
SQL_HOST = os.getenv('SQL_HOST')
# For token
SECRET_KEY = os.getenv("SECRET_KEY")
API_PASSWORD = os.getenv("API_PASSWORD")
ALGORITHM = os.getenv("ALGORITHM")
# Initialize FastAPI app
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# MongoDB connection setup
client = MongoClient(f'mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}?retryWrites=true&w=majority&appName={MONGODB_CLUSTER}')
db = client["pokemon_project_db"]
image_collection = db["Image URL"]
description_collection = db["Descriptions"]

# Connect to MySQL database
conn = connector.connect(
    host=SQL_HOST,
    database='pokemon_project_db',
    user=SQL_USERNAME,
    password=SQL_PASSWORD
)
cursor = conn.cursor(dictionary=True)

# Modèle pour l’authentification
class TokenRequest(BaseModel):
    password: str
    duration: Optional[int] = 3600  

# Function to generate a JWT
def create_jwt(duration: int):
    """
    Generate a JWT token with expiration.
    """
    expiration = datetime.datetime.utcnow() + datetime.timedelta(seconds=duration)
    payload = {"exp": expiration.timestamp()}  # Convert datetime to UNIX timestamp
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# Route pour obtenir un token
@app.post("/token")
def generate_token(request: TokenRequest):
    """
    Fonction/route qui permet de générer un token pour un utilisateur qui saisi son mot de passe
    :param request: Objet TokenRequest
    """
    if request.password != API_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid password")
    token = create_jwt(request.duration)
    return {"token": token}

def verify_token(authorization: Optional[str] = Header(None)):
    if authorization is None:
        raise HTTPException(status_code=401, detail="Missing token")
    
    print(f"Received Authorization Header: {authorization}")  

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0] != "Bearer":
        raise HTTPException(status_code=401, detail="Invalid token format")

    token = parts[1]
    print(f"Extracted Token: {token}")  

    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        print(f"Decoded Token: {decoded}")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/mongo/images")
def get_mongo_images():
    images = list(image_collection.find({}, {"_id": 0}))
    return {"images": images}

@app.get("/mongo/descriptions")
def get_mongo_descriptions():
    descriptions = list(description_collection.find({}, {"_id": 0}))
    return {"descriptions": descriptions}

@app.get("/sql/pokemon")
def get_sql_pokemon():
    query = "SELECT * FROM pokemon"  
    cursor.execute(query)
    records = cursor.fetchall()
    return {"pokemon": records}

@app.get("/pokemon")
def get_pokemon(name: str = Query(..., title="Pokemon Name", description="Enter the Pokémon name to retrieve its information")):
    # fresh SQL connection
    cursor = conn.cursor(dictionary=True)

    # SQL query to fetch Pokémon details, including type(s), ability, and move(s)
    query = """
        SELECT 
            p.pokedex AS pokedex_number, 
            p.name, 
            GROUP_CONCAT(DISTINCT t.type_name) AS type_names,
            GROUP_CONCAT(DISTINCT a.ability_name) AS ability_names,  -- Aggregated ability names
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
    
    print(f"Executing query for Pokémon name: {name}")  # Log the name being queried
    cursor.execute(query, (name,))
    record = cursor.fetchone()
    # conn.close()  

    # Log the record to inspect the query output
    print(f"Query result: {record}")

    if record:
        pokedex_number = record["pokedex_number"]

        # Fetch description from MongoDB
        print(f"Fetching description for Pokedex Number: {pokedex_number}")
        description_data = description_collection.find_one(
            {"Pokedex_Number": pokedex_number}, {"_id": 0, "Description": 1}
        )
        description = description_data["Description"] if description_data else None

        # Fetch image URL from MongoDB
        print(f"Fetching image URL for Pokedex Number: {pokedex_number}")
        image_data = image_collection.find_one(
            {"Pokedex_Number": pokedex_number}, {"_id": 0, "Image URL": 1}
        )
        image_url = image_data["Image URL"] if image_data else None

        # Safely process the type_names, ability_names, and move_names
        types = record["type_names"].split(",") if record.get("type_names") else []
        abilities = record["ability_names"].split(",") if record.get("ability_names") else []
        moves = record["move_names"].split(",") if record.get("move_names") else []

        return {
            "pokemon": {
                "name": record["name"],
                "types": types,
                "abilities": abilities,
                "moves": moves,
                "pokedex_number": pokedex_number,
                "image": image_url,
                "description": description,
            }
        }

    return {"message": "Pokémon not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
