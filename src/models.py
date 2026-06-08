from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class RightsLevel(int, Enum):
    BASIC = 1
    POWER = 2
    ADMIN = 3

class User(BaseModel):
    discord_id: int
    username: str
    avatar: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    boot_rights_level: RightsLevel = RightsLevel.BASIC
    added_date: datetime = Field(default_factory=datetime.now)
    added_by: Optional[int] = None
    notes: Optional[str] = None

    class Config:
        use_enum_values = True

class BootRestrictionType(str, Enum):
    ALWAYS_ALLOW = "always_allow"
    SINGLE_SHOT = "single_shot"
    WORKING_HOURS = "working_hours"

class BootRestriction(BaseModel):
    type: BootRestrictionType
    enabled: bool = True
    config: Dict[str, Any]
    created_date: datetime = Field(default_factory=datetime.now)
    last_modified: datetime = Field(default_factory=datetime.now)

class BootRequest(BaseModel):
    user_id: int
    action: str
    status: str = "pending"
    timestamp: datetime = Field(default_factory=datetime.now)
    host_type: Optional[str] = "hardware"
    host_name: Optional[str] = "claptp"

class HostBootStatus(BaseModel):
    host_type: str
    host_name: str
    status: str
    last_update: datetime = Field(default_factory=lambda: datetime.now())