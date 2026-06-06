import logging
from src.util.db.mongo_client import get_mongo_client

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'mongo_client'):
            self.mongo_client = get_mongo_client()

    @staticmethod
    def get(database: str, collection: str, identifier: dict, return_field: str = None, default=None):
        try:
            manager = DatabaseManager()
            db = manager.mongo_client.get_db(database)
            col = db[collection]

            document = col.find_one(identifier)

            if not document:
                logger.warning(f"No document found in {database}.{collection} matching {identifier}")
                return default

            if return_field is None:
                return document

            keys = return_field.split('.')
            value = document

            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    return default

            return value if value is not None else default

        except Exception as e:
            logger.error(f"Error fetching data from {database}.{collection} with identifier {identifier}: {e}")
            return default

    @staticmethod
    def set(database: str, collection: str, identifier: dict, update_data: dict) -> bool:
        try:
            manager = DatabaseManager()
            db = manager.mongo_client.get_db(database)
            col = db[collection]

            result = col.update_one(identifier, {"$set": update_data}, upsert=True)
            return result.modified_count > 0 or result.upserted_id is not None

        except Exception as e:
            logger.error(f"Error updating data in {database}.{collection} with identifier {identifier}: {e}")
            return False

    @staticmethod
    def delete(database: str, collection: str, identifier: dict) -> bool:
        try:
            manager = DatabaseManager()
            db = manager.mongo_client.get_db(database)
            col = db[collection]

            result = col.delete_one(identifier)
            return result.deleted_count > 0

        except Exception as e:
            logger.error(f"Error deleting data from {database}.{collection} with identifier {identifier}: {e}")
            return False

def get_database_manager() -> DatabaseManager:
    return DatabaseManager()