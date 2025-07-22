import requests
import time
import json
from typing import List, Dict, Any, Optional

from config import GET_DRIVERS_URL, GET_PARTNER_DATA_URL
from schemas.driver_schema import PremiumDriver, DetailedDriver

def get_timestamp():
    """Generates a timestamp in milliseconds."""
    return int(time.time() * 1000)

def make_api_request(url: str, payload: dict) -> Dict[str, Any]:
    """A helper function to make POST requests to the backend with extensive debugging."""
    headers = {"Content-Type": "application/json"}
    
    print("\n" + "="*25 + " API REQUEST SENT " + "="*25)
    print(f"DEBUG: Target URL: {url}")
    print(f"DEBUG: Outgoing Payload:\n{json.dumps(payload, indent=2)}")
    print("="*70)

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        print("\n" + "="*25 + " API RESPONSE RECEIVED " + "="*22)
        print(f"DEBUG: Status Code: {response.status_code}")
        print(f"DEBUG: Raw Response Text:\n{response.text}")
        print("="*70)

        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"!!! DEBUG: HTTP ERROR during API request: {http_err}")
        return {"error": str(http_err), "raw_response": response.text}
    except requests.exceptions.RequestException as e:
        print(f"!!! DEBUG: NETWORK ERROR during API request: {e}")
        return {"error": str(e)}
    except json.JSONDecodeError as json_err:
        print(f"!!! DEBUG: JSON DECODE ERROR - API did not return valid JSON: {json_err}")
        return {"error": "Invalid JSON response from server", "raw_response": response.text}


# The rest of the file remains the same, but will now use the highly verbose make_api_request function.

def fetch_drivers_from_api(city: str, page: int, limit: int) -> List[Dict[str, Any]]:
    """Fetches a paginated list of drivers for a given city from the API."""
    payload = {"city": city, "limit": limit, "page": page, "timestamp": get_timestamp()}
    response_data = make_api_request(GET_DRIVERS_URL, payload)
    
    drivers_raw = response_data.get("data", [])
    
    if not isinstance(drivers_raw, list):
        return []

    for driver in drivers_raw:
        if 'verifiedVehicles' in driver and isinstance(driver['verifiedVehicles'], list):
            for vehicle in driver['verifiedVehicles']:
                if isinstance(vehicle.get('perKmCost'), dict):
                    vehicle['perKmCost'] = None
    try:
        validated_drivers = [PremiumDriver(**driver).dict() for driver in drivers_raw]
        return validated_drivers
    except Exception as e:
        print(f"!!! DEBUG: Pydantic validation failed for PremiumDriver list: {e}")
        return []

def construct_detailed_driver(
    premium_info: Dict[str, Any], 
    details_from_api: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Manually constructs the final DetailedDriver object.
    """
    if not details_from_api:
        return None

    combined_data = {
        "existingInfo": premium_info, "age": details_from_api.get("age"),
        "connections": details_from_api.get("connections", 0), "bio": details_from_api.get("bio"),
        "experience": details_from_api.get("experience", 0), "isPetAllowed": details_from_api.get("isPetAllowed"),
        "languages": details_from_api.get("languages", []), "married": details_from_api.get("married"),
        "phoneNo": details_from_api.get("phoneNo") or premium_info.get("phoneNo"),
        "routes": details_from_api.get("routes", []), "tripTypes": details_from_api.get("tripTypes", []),
        "userName": details_from_api.get("userName") or premium_info.get("userName"),
        "trainingContent": details_from_api.get("trainingContent", []),
        "vehicleOwnership": details_from_api.get("vehicleOwnership", []),
        "verifiedLanguages": details_from_api.get("verifiedLanguages", []),
        "onboardedAt": details_from_api.get("onboardedAt")
    }
    
    try:
        validated_driver = DetailedDriver(**combined_data).dict()
        return validated_driver
    except Exception as e:
        print(f"!!! DEBUG: Pydantic validation failed for constructed DetailedDriver: {e}")
        return None