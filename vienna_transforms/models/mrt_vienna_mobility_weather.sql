WITH transit AS (
    --  Use 'ref' here to grab our clean, deduplicated Silver data
    SELECT * FROM {{ ref('stg_transit') }}
),

weather AS (
    --  Use 'ref' here to grab our clean, deduplicated Silver data
    SELECT * FROM {{ ref('stg_weather') }}
)

-- Because 1 am building a hyper-local dashboard tracking exactly 1 transit stop 
-- and 1 weather station, I will simply combine them into a single row using a CROSS JOIN.
-- (Since the staging models ensure there is only 1 row in each table, 1 x 1 = 1 row!)
SELECT
    t.stop_name,
    t.line_name,
    w.temperature_celsius,
    w.precipitation_mm,
    t.updated_at AS transit_last_updated,
    w.updated_at AS weather_last_updated
FROM transit t
CROSS JOIN weather w