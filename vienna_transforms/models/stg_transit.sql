WITH raw_data AS (
    SELECT * FROM {{ source('vienna_raw', 'raw_transit') }}
),

deduplicated_data AS (
    SELECT 
        stop_id,
        stop_name,
        line_name,
        time_planned,
        time_real,
        delay_seconds,
        CAST(nearest_weather_station_id AS STRING) AS nearest_weather_station_id,
        CAST(ingestion_timestamp AS TIMESTAMP) AS updated_at,
        ROW_NUMBER() OVER (
            PARTITION BY stop_id 
            ORDER BY ingestion_timestamp DESC
        ) as row_num
    FROM raw_data
)

SELECT 
    stop_id,
    stop_name,
    line_name,
    time_planned,
    time_real,
    delay_seconds,
    nearest_weather_station_id,
    updated_at
FROM deduplicated_data
WHERE row_num = 1