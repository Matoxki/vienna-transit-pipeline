import os
import requests
import datetime
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account_key.json"
client = bigquery.Client()

def load_weather_to_bq():
    """Fetches live weather data and loads it into BigQuery."""
    print("Fetching live weather data...")
    url = "https://dataset.api.hub.geosphere.at/v1/station/current/tawes-v1-10min?parameters=TL,RR&station_ids=11035"
    response = requests.get(url)
    
    if response.status_code == 200:
        raw_json = response.json()
        measurements = raw_json['features'][0]['properties']['parameters']
        
        row_to_insert = [
            {
                "temperature": measurements['TL']['data'][0],
                "precipitation": measurements['RR']['data'][0],
                "station_id": "11035",
                # Updated to use modern timezone-aware UTC timestamp
                "ingestion_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        ]
        
        table_id = "data-eng-portfolio-1.raw_vienna_data.raw_weather"
        
        print("Uploading to BigQuery...")
        job_config = bigquery.LoadJobConfig(
            autodetect=True,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND
        )
        
        job = client.load_table_from_json(row_to_insert, table_id, job_config=job_config)
        job.result()
        
        print(f"Success! Loaded {job.output_rows} row(s) into {table_id}.")
        
    else:
        print(f"API Error: {response.status_code}")

if __name__ == "__main__":
    load_weather_to_bq()


def load_transit_to_bq():
    """Fetches live transit data and loads it into BigQuery."""
    print("Fetching live transit data...")
    url = "https://www.wienerlinien.at/ogd_realtime/monitor?stopId=4116"
    response = requests.get(url)
    
    if response.status_code == 200:
        raw_json = response.json()
        
        # Extract the station and line info from the JSON payload
        monitor = raw_json['data']['monitors'][0]
        stop_name = monitor['locationStop']['properties']['title']
        line_name = monitor['lines'][0]['name']
        
        # Create the clean dictionary
        row_to_insert = [
            {
                "stop_id": "4116",
                "stop_name": stop_name,
                "line_name": line_name,
                "ingestion_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
        ]
        
        # Define target table (Notice it's a new table name: raw_transit)
        table_id = "data-eng-portfolio-1.raw_vienna_data.raw_transit"
        
        print("Uploading transit data to BigQuery...")
        job_config = bigquery.LoadJobConfig(
            autodetect=True,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND
        )
        
        job = client.load_table_from_json(row_to_insert, table_id, job_config=job_config)
        job.result()
        
        print(f"Success! Loaded {job.output_rows} row(s) into {table_id}.")
        
    else:
        print(f"API Error: {response.status_code}")

# update the main block to run both functions 
if __name__ == "__main__":
    load_weather_to_bq()
    load_transit_to_bq()