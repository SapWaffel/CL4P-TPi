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
        self.databases = {}
        self.config = ConfigManager.get("mongodb")
        
        uri = self.config.get("uri")
        self._connect(uri)
        self._initialized = True
    
    def _connect(self, connection_string: str):
        try:
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
            
            # Load databases and collections from config
            db_configs = self.config.get("databases", [])
            
            for db_config in db_configs:
                db_name = db_config.get("name")
                self.databases[db_name] = self.client[db_name]
                logger.info(f"Connected to MongoDB database: {db_name}")
            
            self._ensure_collections()
        
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    

    def _ensure_collections(self) -> None:
        db_configs = self.config.get("databases", [])

        for db_config in db_configs:
            db_name = db_config.get("name")
            collections = db_config.get("collections", [])
            db = self.databases[db_name]
            
            for collection_config in collections:
                collection_name = collection_config if isinstance(collection_config, str) else collection_config.get("name")
                
                if collection_name not in db.list_collection_names():
                    db.create_collection(collection_name)
                    logger.info(f"Created collection '{collection_name}' in database '{db_name}'")
                
                # Create indexes if collection_config is a dict with indexes
                if isinstance(collection_config, dict):
                    self._create_indexes(db[collection_name], collection_config)

    
    def _create_indexes(self, collection, collection_config: dict):
        indexes = collection_config.get("indexes", [])
        
        if not indexes:
            return
        
        for index_config in indexes:
            fields = index_config.get("fields")
            unique = index_config.get("unique", False)
            collection.create_index(fields, unique=unique)
            logger.info(f"Created index on collection {collection.name}: fields={fields}, unique={unique}")

    def get_db(self, db_name: str = "discord"):
        if db_name not in self.databases:
            raise ValueError(f"Database '{db_name}' not found.")
        
        if self.databases[db_name] is None:
            raise RuntimeError(f"Database '{db_name}' not connected")
        
        return self.databases[db_name]
    
    def disconnect(self) -> None:
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

def get_mongo_client() -> MongoDBClient:
    return MongoDBClient()