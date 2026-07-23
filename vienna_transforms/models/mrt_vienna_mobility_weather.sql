WITH transit AS (
    -- Grab our clean, deduplicated Silver data from the transit staging model
    SELECT * FROM {{ ref('stg_transit') }}
),

weather AS (
    -- Grab our clean, deduplicated Silver data from the weather staging model
    SELECT * FROM {{ ref('stg_weather') }}
)

-- Instead of a global CROSS JOIN which duplicates un-related data,
-- we now perform an explicit INNER JOIN using our relational station mapping key!
SELECT
    t.stop_id,
    t.stop_name,
    t.line_name,
    t.time_planned,
    t.time_real,
    t.delay_seconds,
    w.station_id AS matched_weather_station_id,
    w.temperature AS temperature_celsius,
    w.precipitation AS precipitation_mm,
    t.updated_at AS transit_last_updated,
    w.updated_at AS weather_last_updated
FROM transit t
INNER JOIN weather w 
    ON t.nearest_weather_station_id = w.station_id