import logging 
from datetime import datetime
from src.util.db.mongo_client import get_mongo_client

logger = logging.getLogger(__name__)

class UserService:

    def __init__(self):
        self.db = get_mongo_client().get_db()
        self.collection = self.db["user"]
    
    def sync_or_create_user(self, discord_id: int, username: str, avatar: str = None, roles: list = None):
        try:
            user_data = {
                "discord_id": discord_id,
                "username": username,
                "avatar": avatar,
                "roles": roles or [],
                "rights_level": 1,
                "added_date": datetime.now(),
                "notes": None,
            }

            result = self.collection.update_one(
                {"discord_id": discord_id},
                {"$set": user_data},
                upsert=True
            )

            return {"success": True, "user_id": discord_id}
        except Exception as e:
            logger.error(f"Error syncing/creating user {discord_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def get_user(self, discord_id: int):
        try:
            user = self.collection.find_one({"discord_id": discord_id})
            return {"success": True, "user": user}
        except Exception as e:
            logger.error(f"Error fetching user {discord_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def get_all_users(self):
        try:
            users = list(self.collection.find())
            return {"success": True, "users": users}
        except Exception as e:
            logger.error(f"Error fetching all users: {e}")
            return {"success": False, "error": str(e)}