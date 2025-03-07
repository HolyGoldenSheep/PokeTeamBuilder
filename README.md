# Pokemon Team Builder

## Description
The **Pokemon Team Builder** is an AI-powered tool designed to generate strategic Pokémon teams for various use cases, including competitive play, Gym Leader battles, and fun random team compositions. This project involves web scraping, public APIs, and database management using both SQL and NoSQL.

## Table of Contents
- [Technologies Used](#technologies-used)
- [Project Setup](#project-setup)
- [Data Acquisition](#data-acquisition)
- [Database Setup](#database-setup)
- [API Setup](#api-setup)
- [Automating the Process](#automating-the-process)
- [Running the Application](#running-the-application)

## Technologies Used
- **Python Libraries**: `os`, `ast`, `pandas`, `mysql.connector`, `pymongo`, `dotenv`, `requests`, `BeautifulSoup`, `csv`, `jwt`, `datetime`
- **Frameworks**: `FastAPI`
- **Databases**: MySQL (SQL) & MongoDB (NoSQL)
- **Web Scraping**: `Requests`, `BeautifulSoup`
- **Public API**: PokéAPI
- **Authentication**: JWT
- **Task Automation**: `crontab`

---

## Project Setup
### 1. Clone the Repository
```bash
git clone <repository-url>
cd pokemon-team-builder
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate   # On macOS/Linux
venv\Scripts\activate      # On Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a `.env` file and add the following:
```env
MYSQL_HOST=your_mysql_host
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=your_db_name
MONGO_URI=mongodb+srv://your_mongo_connection
SECRET_KEY=your_secret_key
```

---

## Data Acquisition
### 1. Web Scraping Pokémon Data
Run the web scraping script to collect Pokémon data from selected websites.
```bash
python "name of your script".py
```
This script will:
- Extract Pokémon names, types, images, and descriptions.
- Save them into `CSV` files for later database insertion.

### 2. Fetch Additional Data via PokéAPI
```bash
python "name of your script".py
```
This script will:
- Retrieve Pokémon abilities and moves from the PokéAPI.
- Store them in a structured `CSV` file.

---

## Database Setup
### 1. MySQL Database
Ensure MySQL is installed and running. Then, execute:
```bash
python setup_mysql.py
```
This script will:
- Create tables for Pokémon, abilities, types, and moves.
- Populate the tables with data extracted from `CSV` files.

### 2. MongoDB Setup
Ensure MongoDB is running, then run:
```bash
python setup_mongodb.py
```
This script will:
- Store Pokémon descriptions and images in MongoDB collections.

---

## API Setup
### 1. Start the FastAPI Server
```bash
uvicorn main:app --reload
```
### 2. API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/pokemon/{name}` | GET | Retrieve Pokémon details |
| `/pokemon/type/{type}` | GET | Get Pokémon by type |
| `/pokemon/move/{move}` | GET | Find Pokémon that can learn a move |
| `/pokemon/ability/{ability}` | GET | Get Pokémon with a specific ability |
| `/auth/token` | POST | Generate JWT token for authentication |

---

## Automating the Process
To run data scraping and API fetching automatically at the end of each year, set up a **cron job** (Linux/macOS) or a **Task Scheduler** (Windows).

Example cron job to run scripts on December 31st:
```cron
0 0 31 12 * /usr/bin/python3 /"path to your script"/"name of your script".py
```

---

## Running the Application
1. **Ensure Databases are Running** (MySQL & MongoDB)
2. **Start the FastAPI Server**
```bash
fastapi dev "name of your script".py
```
3. **Access the API Documentation**
Visit `http://127.0.0.1:8000/docs` for interactive API testing.

---

## Contributors
- **Author**: Karl Benton

## License
This project is licensed under the MIT License.



