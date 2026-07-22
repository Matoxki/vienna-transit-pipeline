WITH raw_data AS (
    -- dbt uses the Address Book here to find the raw table!
    SELECT * 
    FROM {{ source('vienna_raw', 'raw_transit') }}
),

deduplicated_data AS (
    SELECT
        stop_id,
        stop_name,
        line_name,
        -- Cast the string timestamp from Python into a true BigQuery Timestamp
        CAST(ingestion_timestamp AS TIMESTAMP) AS updated_at,
        
        -- The Magic Window Function:
        -- It groups by the station and line, sorts by the newest time, and assigns row #1 to the newest record.
        ROW_NUMBER() OVER (
            PARTITION BY stop_id, line_name 
            ORDER BY ingestion_timestamp DESC
        ) as row_num
    FROM raw_data
)

-- Filter to ONLY keep the newest record (row_num = 1)
SELECT
    stop_id,
    stop_name,
    line_name,
    updated_at
FROM deduplicated_data
WHERE row_num = 1