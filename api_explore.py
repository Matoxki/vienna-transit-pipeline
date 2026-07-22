import requests
import json

def fetch_transit_data():
    """
    Extracts real-time transit departures from Wiener Linien.
    We are using the 'monitor' endpoint and filtering for stopId=4116 (Stephansplatz U1).
    """
    transit_url = "https://www.wienerlinien.at/ogd_realtime/monitor?stopId=4116"
    
    print("--- Fetching Vienna Transit Data ---")
    response = requests.get(transit_url)
    
    # Status code 200 means "OK" / Success
    if response.status_code == 200:
        transit_data = response.json()
        print("Success! Here is the raw location data for this stop:")
        # We navigate the JSON dictionary to print just the location details
        print(json.dumps(transit_data['data']['monitors'][0]['locationStop'], indent=2))
    else:
        print(f"Failed to fetch data. Error: {response.status_code}")

def fetch_weather_data():
    """
    Extracts live 10-minute weather data from GeoSphere Austria.
    We are targeting station 11035 (Wien/Hohe Warte) and asking for TL (Temperature) and RR (Precipitation).
    """
    weather_url = "https://dataset.api.hub.geosphere.at/v1/station/current/tawes-v1-10min?parameters=TL,RR&station_ids=11035"
    
    print("\n--- Fetching Vienna Weather Data ---")
    response = requests.get(weather_url)
    
    if response.status_code == 200:
        weather_data = response.json()
        print("Success! Here are the requested weather parameters (Temp & Precipitation):")
        # We navigate the JSON dictionary to print just the weather readings
        print(json.dumps(weather_data['features'][0]['properties']['parameters'], indent=2))
    else:
        print(f"Failed to fetch data. Error: {response.status_code}")

# This tells Python to run our two functions when we execute the script
if __name__ == "__main__":
    fetch_transit_data()
    fetch_weather_data()