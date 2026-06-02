import logging
from src.db.mongo_client import get_mongo_client

logger = logging.getLogger(__name__)

class RestrictionService:
    def __init__(self):
        self.db = get_mongo_client().get_db()
        self.collection = self.db["boot_restriction"]
    
    def get_all_restrictions(self):
        try:
            restrictions = list(self.collection.find({"enabled": True}))
            logger.info(f"Loaded {len(restrictions)} restrictions from the database.")
            return {"success": True, "restrictions": restrictions}
        except Exception as e:
            logger.error(f"Error loading restrictions: {e}")
            return {"success": False, "error": str(e)}
    
    def get_restriction_by_type(self, restriction_type):
        try:
            restriction = self.collection.find_one({"type": restriction_type, "enabled": True})
            if restriction:
                return {"success": True, "restriction": restriction}
            return {"success": False, "error": "Restriction not found"}
        except Exception as e:
            logger.error(f"Error loading restriction by type: {e}")
            return {"success": False, "error": str(e)}