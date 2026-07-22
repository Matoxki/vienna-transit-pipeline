WITH raw_data AS (
    SELECT * 
    FROM {{ source('vienna_raw', 'raw_weather') }}
),

deduplicated_data AS (
    SELECT
        station_id,
        -- Explicitly casting to FLOAT64 to ensure math works later
        CAST(temperature AS FLOAT64) AS temperature_celsius,
        CAST(precipitation AS FLOAT64) AS precipitation_mm,
        CAST(ingestion_timestamp AS TIMESTAMP) AS updated_at,
        
        -- The same deduplication magic for the weather station
        ROW_NUMBER() OVER (
            PARTITION BY station_id 
            ORDER BY ingestion_timestamp DESC
        ) as row_num
    FROM raw_data
)

SELECT
    station_id,
    temperature_celsius,
    precipitation_mm,
    updated_at
FROM deduplicated_data
WHERE row_num = 1