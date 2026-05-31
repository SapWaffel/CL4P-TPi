import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from src.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class MongoDBClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self.client = None
        self.db = None
    
        uri = ConfigManager.get_config("mongodb.uri")
        db_name = ConfigManager.get_config("mongodb.database")

        self.connect(uri, db_name)
        self._initialized = True
    
    def connect(self, connection_string: str, db_name: str = "discord") -> bool:
        try:
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
            self.db = self.client[db_name]

            logger.info("Successfully connected to MongoDB")
            self._ensure_collections()
            return True
        
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.client = None
            self.db = None
            return False
        
        except Exception as e:
            logger.error(f"An error occurred while connecting to MongoDB: {e}")
            self.client = None
            self.db = None
            return False

    def _ensure_collections(self) -> None:
        if self.db is None:
            logger.error("Database connection is not established.")
            return
        
        if "user" not in self.db.list_collection_names():
            self.db.create_collection("user")
            self.db.user.create_index("discord_id", unique=True)
        
        if "boot_restriction" not in self.db.list_collection_names():
            self.db.create_collection("boot_restriction")

        if "boot_request" not in self.db.list_collection_names():
            self.db.create_collection("boot_request")
            self.db.boot_request.create_index("timestamp")
    
    def disconnect(self) -> None:
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
            self.client = None
            self.db = None
    
    def get_db(self):
        if self.db is None:
            raise RuntimeError("Database connection is not established.")
        return self.db
    
def get_mongo_client() -> MongoDBClient:
    return MongoDBClient()