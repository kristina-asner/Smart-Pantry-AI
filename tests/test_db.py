import os
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi

# load environment variables from .env file
load_dotenv()

def connect_to_pantry():
    uri = os.getenv("MONGO_URI")
    try:
        #connect to MongoDB using the URI and certifi for SSL
        client = MongoClient(uri, tlsCAFile=certifi.where())
        
        # check the connection by pinging the server
        client.admin.command('ping')
        print("✅ mongo is connected!")
        
        # check available databases to confirm connection
        print("Databases available:", client.list_database_names())
        
    except Exception as e:
        print(f"❌ connection failed: {e}")

if __name__ == "__main__":
    connect_to_pantry()