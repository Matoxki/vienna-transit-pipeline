WITH raw_data AS (
    SELECT * FROM {{ source('vienna_raw', 'raw_weather') }}
),

deduplicated_data AS (
    SELECT 
        -- Force this column to be a String so it matches the transit table safely
        CAST(station_id AS STRING) AS station_id,
        temperature,
        precipitation,
        CAST(ingestion_timestamp AS TIMESTAMP) AS updated_at,
        ROW_NUMBER() OVER (
            PARTITION BY station_id 
            ORDER BY ingestion_timestamp DESC
        ) as row_num
    FROM raw_data
)

SELECT 
    station_id,
    temperature,
    precipitation,
    updated_at
FROM deduplicated_data
WHERE row_num = 1