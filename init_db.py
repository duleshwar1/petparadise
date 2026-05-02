import os
import urllib.parse
import pymysql
from pymysql.constants import CLIENT
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

def init_database():
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("Error: DATABASE_URL environment variable is not set.")
        print("Please set it before running this script.")
        return

    print("Parsing DATABASE_URL...")
    url = urllib.parse.urlparse(database_url)
    
    db_host = url.hostname
    db_user = url.username
    db_password = url.password
    db_name = url.path[1:] # Remove leading slash
    db_port = url.port or 3306

    print(f"Connecting to database '{db_name}' at {db_host}:{db_port}...")

    try:
        # Connect to the database with CLIENT.MULTI_STATEMENTS to allow running the full SQL script at once
        connection = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            port=db_port,
            client_flag=CLIENT.MULTI_STATEMENTS
        )
        
        sql_file_path = os.path.join('database', 'pet_store.sql')
        
        if not os.path.exists(sql_file_path):
            print(f"Error: SQL file not found at {sql_file_path}")
            return
            
        print(f"Reading SQL script from {sql_file_path}...")
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        print("Executing SQL script...")
        with connection.cursor() as cursor:
            cursor.execute(sql_script)
            connection.commit()
            
        print("Database initialized successfully! All tables and sample data have been created.")

    except pymysql.MySQLError as e:
        print(f"Database error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
            print("Database connection closed.")

if __name__ == "__main__":
    init_database()
