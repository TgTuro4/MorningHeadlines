import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GeocodingService:
    """Service for interacting with Google Maps Geocoding API"""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        
    async def get_location_from_coordinates(self, latitude, longitude):
        """
        Convert coordinates to a location name using Google's Geocoding API
        
        Args:
            latitude (float): The latitude coordinate
            longitude (float): The longitude coordinate
            
        Returns:
            dict: Location information including city, region, country
        """
        try:
            params = {
                "latlng": f"{latitude},{longitude}",
                "key": self.api_key,
                "result_type": "locality|administrative_area_level_1|country"
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data["status"] != "OK":
                return {"error": f"Geocoding API error: {data['status']}"}
                
            # Extract location components
            location = {
                "city": None,
                "region": None,
                "country": None,
                "country_code": None,
                "formatted_address": None
            }
            
            if data["results"]:
                # Get the first result's formatted address
                location["formatted_address"] = data["results"][0]["formatted_address"]
                
                # Extract components
                for result in data["results"]:
                    for component in result["address_components"]:
                        if "locality" in component["types"]:
                            location["city"] = component["long_name"]
                        elif "administrative_area_level_1" in component["types"]:
                            location["region"] = component["long_name"]
                        elif "country" in component["types"]:
                            location["country"] = component["long_name"]
                            location["country_code"] = component["short_name"]
            
            return location
            
        except Exception as e:
            return {"error": f"Geocoding service error: {str(e)}"}
