import os

NUTRITIONIX_BASE_URL = "https://trackapi.nutritionix.com/v2"
WGER_BASE_URL = "https://wger.de/api/v2"

NUTRITIONIX_APP_ID = os.getenv("NUTRITIONIX_APP_ID")
NUTRITIONIX_APP_KEY = os.getenv("NUTRITIONIX_APP_KEY")

def get_nutritionix_headers():
    return {
        "x-app-id": NUTRITIONIX_APP_ID,
        "x-app-key": NUTRITIONIX_APP_KEY,
        "Content-Type": "application/json"
    }

def get_wger_headers():
    return {
        "Accept": "application/json",
        "User-Agent": "Fitness-Nutrition-MCP-Server/1.0"
    } 