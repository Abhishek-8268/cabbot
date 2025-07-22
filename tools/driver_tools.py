from typing import Dict, Optional, Any
from langchain_core.tools import tool

@tool
def set_city(city: str) -> Dict[str, str]:
    """
    Use this tool to set or update the user's city when they specify one.
    This should be your first step if the city is not already set or if the user names a new city.
    """
    print(f"--- TOOL: Setting city to {city} ---")
    return {"city_updated": city}

@tool
def find_drivers(city: str) -> Dict[str, Any]:
    """
    Finds the NEXT page of available drivers for a given city to add to the local cache.
    Use this when the user asks to see more drivers, or when a filter comes up empty.
    """
    print(f"--- TOOL: Finding more drivers in {city} ---")
    return {"city": city}

# --- NEW FILTERING TOOL ---
@tool
def filter_drivers(language: Optional[str] = None, pets_allowed: Optional[bool] = None, married: Optional[bool] = None) -> Dict[str, Any]:
    """
    Filters the currently cached list of drivers based on user preferences like language, pet policy, or marital status.
    Call this tool whenever a user expresses a preference.
    """
    print(f"--- TOOL: Applying filters: lang='{language}', pets='{pets_allowed}', married='{married}' ---")
    
    # The tool itself just returns the filters. The tool_node will perform the actual filtering logic.
    active_filters = {}
    if language is not None:
        active_filters['languages'] = language.lower()
    if pets_allowed is not None:
        active_filters['isPetAllowed'] = pets_allowed
    if married is not None:
        active_filters['married'] = married
        
    return {"filters_to_apply": active_filters}

# The user-facing get_driver_details tool is removed, as it's now an internal process.
# We keep a simple tool for the final step.
@tool
def get_driver_contact_info(driver_id: str) -> Dict[str, str]:
    """
    Use this as the final step to get the contact number for a specific driver when the user confirms they want to book.
    """
    print(f"--- TOOL: Getting contact info for driver_id: {driver_id} ---")
    return {"driver_id_for_contact": driver_id}


tools = [set_city, find_drivers, filter_drivers, get_driver_contact_info]