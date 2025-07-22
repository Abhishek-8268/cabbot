from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

# --- NO CHANGES TO DRIVER SCHEMAS ---
class VerifiedVehicle(BaseModel):
    reg_no: str
    model: str
    is_commercial: Optional[bool] = None
    perKmCost: Optional[float] = None
    vehicleType: str

class PremiumDriver(BaseModel):
    id: str
    name: Optional[str] = None
    city: Optional[str] = None
    phoneNo: str
    profile_image: Optional[str] = ""
    userName: Optional[str] = None
    verifiedVehicles: List[VerifiedVehicle] = []

class DetailedDriver(BaseModel):
    existingInfo: PremiumDriver
    age: Optional[int] = None
    connections: int = 0
    bio: Optional[Union[str, List[str]]] = None
    experience: int = 0
    isPetAllowed: Optional[bool] = None
    languages: List[str] = []
    married: Optional[bool] = None
    phoneNo: str
    routes: List[Dict[str, str]] = []
    tripTypes: List[str] = []
    userName: Optional[str] = None
    trainingContent: List[Dict[str, str]] = []
    vehicleOwnership: List[bool] = []
    verifiedLanguages: List[Dict[str, Any]] = []
    onboardedAt: Optional[str] = None

# --- AGENTSTATE IS ENHANCED ---
class AgentState(BaseModel):
    """
    Represents the state of our cab booking agent.
    """
    messages: List[Any] = Field(default_factory=list)
    city: Optional[str] = None
    page: int = 1
    filters: Dict[str, Any] = Field(default_factory=dict)
    
    # The master cache of all drivers we have fetched, keyed by ID.
    # This will now store the full DetailedDriver profile.
    driver_profiles: Dict[str, Dict] = Field(default_factory=dict)
    
    # A list of driver IDs that have already been presented to the user.
    # This prevents showing the same driver twice.
    presented_driver_ids: List[str] = Field(default_factory=list)
    
    # A counter for the recursive filtering process.
    filter_search_depth: int = 0
    
    no_more_drivers: bool = False