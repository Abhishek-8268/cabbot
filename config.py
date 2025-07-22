import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CABSWALE_API_KEY = os.getenv("CABSWALE_API_KEY")

# API Endpoints
BASE_URL = "https://us-central1-cabswale-ai.cloudfunctions.net"
GET_DRIVERS_URL = f"{BASE_URL}/typesense-getPartnersByLocation"
GET_PARTNER_DATA_URL = f"{BASE_URL}/partners-getPartnerData"

# --- UPDATED SEARCH DEFAULTS ---
# Fetch 10 drivers at a time to build a larger local cache
DEFAULT_PAGE_LIMIT = 10
# Set the maximum number of pages to fetch when a filter finds no results
MAX_FILTER_DEPTH = 5