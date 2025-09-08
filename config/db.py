from flask_mysqldb import MySQL
import os
from dotenv import load_dotenv

# Get the .env file 
load_dotenv()

# MySQL instance
mysql = MySQL()

# Function to connect to the database
def init_db(app):
    '''Configure the database with the flask instance (app)'''
    app.config['MYSQL_HOST'] = os.getenv("DB_HOST")
    app.config['MYSQL_USER'] = os.getenv("DB_USER")
    app.config['MYSQL_PASSWORD'] = os.getenv("DB_PASSWORD")
    app.config['MYSQL_DB'] = os.getenv("DB_NAME")
    app.config['MYSQL_PORT'] = int(os.getenv("DB_PORT"))
    
    # Initialize the connection
    mysql.init_app(app)
    
# Define the cursor
def get_db_connection():
    '''Return the cursor to interact with the DB'''
    try:
        connection = mysql.connection
        return connection.cursor()
    except Exception as e:
        raise RuntimeError(f"Error, could not connect to the database: {e}")
