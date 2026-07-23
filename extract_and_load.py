import os
import time
import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timezone

#  1. Authenticate & Setup 
# Before we can talk to Google Cloud, we need to prove who we are.
# Checking if our secret "service_account_key.json" file exists on the computer.
# If it does, setting an environment variable so the Google library can find it and log us in automatically.
if os.path.exists("service_account_key.json"):
    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "service_account_key.json")

# Defining the exact Google Cloud Project and the Dataset (folder) where our tables live.
PROJECT_ID = "data-eng-portfolio-1"
DATASET_ID = "raw_vienna_data"

# Setting up safety rules for our internet requests.
# If a website doesn't respond in 10 seconds, we stop waiting so the script doesn't freeze forever.
REQUEST_TIMEOUT = 10  
MAX_RETRIES = 3       # We will try a failing website a maximum of 3 times before giving up.
RETRY_DELAY = 2       # We will wait 2 seconds before the first retry (this gets longer each time).

#  2. The Vienna Station Network 
# Creating a list (or "dictionary") of the 5 major Vienna transit stops we want to monitor.
# For each stop, providing its specific transit ID (rbl) and matching it to the closest weather station ID.
# Station 11034 is "Wien City" (used for central/southern stops).
# Station 11035 is "Wien Hohe Warte" (used for northern/western stops).
STATION_MAPPINGS = [
    {"stop_name": "Karlsplatz (U1/U2/U4)", "transit_rbl": "3111", "weather_station_id": "11034"},
    {"stop_name": "Landstraße (U3/U4)", "transit_rbl": "4101", "weather_station_id": "11034"},
    {"stop_name": "Stephansplatz (U1/U3)", "transit_rbl": "4210", "weather_station_id": "11034"},
    {"stop_name": "Westbahnhof S U", "transit_rbl": "36", "weather_station_id": "11035"},
    {"stop_name": "Praterstern S U", "transit_rbl": "311", "weather_station_id": "11035"},
]


def parse_wiener_linien_timestamp(ts_str):
    """
    Helper Function: The transit API gives us time in a very specific text format.
    This function converts that text into a real 'datetime' object that Python understands, 
    making sure to handle the Vienna timezone offset properly.
    """
    if not ts_str:
        return None
    return datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S.%f%z")


def make_resilient_request(url):
    """
    Helper Function: A safer way to visit websites.
    Instead of crashing the whole program if a website is down or slow, this function tries to visit the URL.
    If it fails, it waits a few seconds and tries again. It doubles the wait time after every failure
    (Exponential Backoff) to avoid overwhelming the server.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Trying to get the data, but giving up if it takes longer than 10 seconds.
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status() # Checking if the website returned an error code (like a 404 Not Found).
            return response
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            print(f"    [Warning] Request failed (Attempt {attempt}/{MAX_RETRIES}) for URL: {url}. Error: {e}")
            if attempt == MAX_RETRIES:
                print("    [Error] Max retries reached. Skipping request.")
                return None
            # Waiting before retrying (2 seconds, then 4 seconds, etc.)
            time.sleep(RETRY_DELAY * (2 ** (attempt - 1)))
    return None


def fetch_transit_data_for_station(stop_info):
    """
    Main Logic: Goes to the Wiener Linien API for a specific station, reads the complex JSON data,
    and extracts only the details we care about (like the train line and how late it is).
    """
    stop_name = stop_info["stop_name"]
    rbl = stop_info["transit_rbl"]
    print(f"\nFetching Live Transit Data ({stop_name})...")

    # Building the exact web address for this specific station.
    transit_url = f"https://www.wienerlinien.at/ogd_realtime/monitor?rbl={rbl}"
    response = make_resilient_request(transit_url)
    if not response:
        return None # Exiting safely if the website never responded.

    try:
        # Converting the website text into a structured JSON dictionary.
        transit_json = response.json()
        monitors = transit_json.get("data", {}).get("monitors", [])
        
        # Checking if there are any trains currently running at this station (crucial for late nights).
        if not monitors:
            print(f"  -> Warning: No monitors found for {stop_name}. (Trains may not be running)")
            return None

        # Digging deep into the JSON layers to find the exact stop ID and name.
        first_monitor = monitors[0]
        stop_id = str(first_monitor.get("locationStop", {}).get("properties", {}).get("name", "Unknown"))
        fetched_stop_title = first_monitor.get("locationStop", {}).get("properties", {}).get("title", stop_name)

        # Checking if there are active transit lines listed.
        lines = first_monitor.get("lines", [])
        if not lines:
            print(f"  -> Warning: No lines found at {stop_name}.")
            return None

        # Grabbing the name of the first train line (e.g., 'U1' or 'N24').
        first_line = lines[0]
        line_name = first_line.get("name", "Unknown")
        departures = first_line.get("departures", {}).get("departure", [])

        time_planned_str = None
        time_real_str = None
        delay_seconds = None

        if departures:
            # Grabbing the planned schedule time and the actual live GPS time.
            departure_time_obj = departures[0].get("departureTime", {})
            time_planned_str = departure_time_obj.get("timePlanned")
            time_real_str = departure_time_obj.get("timeReal")

            # Converting the text strings into real Python times.
            time_planned = parse_wiener_linien_timestamp(time_planned_str)
            time_real = parse_wiener_linien_timestamp(time_real_str)

            # Calculating the live delay in seconds by subtracting the planned time from the real time.
            # (If a train is early, this number will be negative).
            if time_planned and time_real:
                delay_seconds = (time_real - time_planned).total_seconds()

        print(f"  -> Success: Pulled {line_name} at {fetched_stop_title}. Delay: {delay_seconds} seconds.")

        # Returning a clean, flat dictionary containing only our final data points.
        return {
            "stop_id": stop_id,
            "stop_name": fetched_stop_title,
            "line_name": line_name,
            "time_planned": time_planned_str,
            "time_real": time_real_str,
            "delay_seconds": delay_seconds,
            "nearest_weather_station_id": stop_info["weather_station_id"],
            "ingestion_timestamp": datetime.now(timezone.utc).isoformat(), # Adding a stamp for exactly when we pulled this
        }

    except Exception as e:
        print(f"  -> Error parsing transit JSON for {stop_name}: {e}")
        return None


def fetch_weather_data_for_station(station_id):
    """
    Main Logic: Goes to the GeoSphere Austria API for a specific weather station, reads the JSON,
    and pulls out the live temperature and precipitation.
    """
    print(f"\nFetching Live Weather Data (Station ID: {station_id})...")
    
    # Building the exact web address for this specific weather station.
    weather_url = f"https://dataset.api.hub.geosphere.at/v1/station/current/tawes-v1-10min?parameters=TL&parameters=RR&station_ids={station_id}"

    response = make_resilient_request(weather_url)
    if not response:
        return None

    try:
        # Converting the website response into a JSON dictionary.
        weather_json = response.json()
        features = weather_json.get("features", [])
        if not features:
            print(f"  -> Warning: No features found for weather station {station_id}.")
            return None

        # Drilling down to find the 'TL' (Temperature) and 'RR' (Rain/Precipitation) values.
        params = features[0].get("properties", {}).get("parameters", {})
        temp = params.get("TL", {}).get("data", [None])[0]
        precip = params.get("RR", {}).get("data", [None])[0]

        print(f"  -> Success: Station {station_id} Temp: {temp}°C, Precip: {precip}mm.")

        # Returning a clean dictionary with our final weather metrics.
        return {
            "station_id": str(station_id),
            "temperature": float(temp) if temp is not None else None,
            "precipitation": float(precip) if precip is not None else None,
            "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        print(f"  -> Error parsing weather JSON for station {station_id}: {e}")
        return None


def load_to_bigquery(client, table_name, dataframe):
    """
    Helper Function: Takes our clean table (Pandas DataFrame) and uploads it securely into Google BigQuery.
    """
    # If a station was offline and our table is empty, we skip the upload process completely.
    if dataframe.empty:
        print(f" -> Skipping {table_name} (No data to load).")
        return

    # Setting up the exact rules for how BigQuery should handle this new data.
    # WRITE_APPEND means "Add these new rows to the bottom of the existing table, keeping our historical log safe."
    # ALLOW_FIELD_ADDITION means "If my Python script sends a brand new column tomorrow, don't crash; just add the column automatically."
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION],
    )

    # Building the exact address for where this table lives in Google Cloud.
    full_table_path = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    print(f" -> Uploading {len(dataframe)} rows to {table_name}...")

    try:
        # Pushing the data to the cloud and waiting for the Google servers to say "Done."
        job = client.load_table_from_dataframe(dataframe, full_table_path, job_config=job_config)
        job.result()
        print("    Done.")
    except Exception as e:
        print(f"    Failed to upload {table_name}: {e}")


def main():
    """
    The Engine: This is the main orchestrator that runs when you execute the script.
    It loops through all stations, coordinates the data fetching, and finally sends everything to BigQuery.
    """
    print("Initializing multi-station extraction with monitoring logs...")
    
    # Starting the engine that talks to Google Cloud.
    client = bigquery.Client()

    # Creating empty lists to hold all the individual rows of data we collect.
    transit_rows = []
    weather_rows = []
    
    # Creating a set to remember which weather stations we have already checked.
    # If 3 transit stops share the same weather station, we only want to ask the weather API once to save time!
    processed_stations = set()

    stations_attempted = len(STATION_MAPPINGS)
    stations_succeeded = 0

    # Looping through every single transit stop in our network dictionary.
    for stop_info in STATION_MAPPINGS:
        
        # 1. Fetching the transit data for this stop
        transit_record = fetch_transit_data_for_station(stop_info)
        if transit_record:
            transit_rows.append(transit_record)
            stations_succeeded += 1

        # 2. Checking the required weather station for this stop
        w_id = stop_info["weather_station_id"]
        
        # If we haven't checked this weather station yet today, fetch it and add it to our list.
        if w_id not in processed_stations:
            weather_record = fetch_weather_data_for_station(w_id)
            if weather_record:
                weather_rows.append(weather_record)
                processed_stations.add(w_id) # Marking it as "Done" so we don't fetch it again.

    # Printing a quick summary of how the pipeline performed.
    print("\n--- Pipeline Health Monitoring Summary ---")
    print(f"Stations Attempted : {stations_attempted}")
    print(f"Stations Succeeded : {stations_succeeded}")
    print(f"Stations Failed    : {stations_attempted - stations_succeeded}")
    print("------------------------------------------")

    # Converting our lists of dictionaries into Pandas DataFrames (clean, Excel-like tables).
    transit_df = pd.DataFrame(transit_rows)
    weather_df = pd.DataFrame(weather_rows)

    # CRITICAL FIX: Explicitly forcing our number columns to be 'floats' (decimals).
    # If a station is offline, its delay_seconds is 'None'. If the very first row is 'None', 
    # the uploader gets confused and crashes. This safely forces everything into a number format.
    if not transit_df.empty:
        transit_df["delay_seconds"] = transit_df["delay_seconds"].astype(float)
    if not weather_df.empty:
        weather_df["temperature"] = weather_df["temperature"].astype(float)
        weather_df["precipitation"] = weather_df["precipitation"].astype(float)

    # Passing our finalized tables to the upload function to send them to Google BigQuery.
    print("\nStarting BigQuery Upload...")
    load_to_bigquery(client, "raw_transit", transit_df)
    load_to_bigquery(client, "raw_weather", weather_df)

    print("\nMulti-station pipeline execution complete.")

# This line ensures that the 'main()' function only runs if we run this script directly 
# (rather than importing it into another file).
if __name__ == "__main__":
    main()