
-- 1. City dimension
CREATE TABLE IF NOT EXISTS dim_city (
    city_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    city_name TEXT NOT NULL UNIQUE,
    latitude NUMERIC(9, 6) NOT NULL,
    longitude NUMERIC(9, 6) NOT NULL,
    timezone TEXT NOT NULL DEFAULT 'Asia/Kolkata',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_city_latitude
        CHECK (latitude BETWEEN -90 AND 90),
    CONSTRAINT chk_city_longitude
        CHECK (longitude BETWEEN -180 AND 180)
);

-- 2. Pipeline ingestion runs
CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'running',
    cities_requested INTEGER NOT NULL DEFAULT 0,
    cities_succeeded INTEGER NOT NULL DEFAULT 0,
    cities_failed INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,

    CONSTRAINT chk_run_status
        CHECK (status IN ('running', 'success', 'partial_failure', 'failed')),
    CONSTRAINT chk_run_counts
        CHECK (
            cities_requested >= 0
            AND cities_succeeded >= 0
            AND cities_failed >= 0
        )
);

-- 3. Raw API responses
CREATE TABLE IF NOT EXISTS raw_api_responses (
    raw_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id BIGINT NOT NULL
        REFERENCES ingestion_runs(run_id),
    city_id INTEGER NOT NULL
        REFERENCES dim_city(city_id),
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    http_status INTEGER,
    payload JSONB NOT NULL,

    CONSTRAINT chk_http_status
        CHECK (
            http_status IS NULL
            OR http_status BETWEEN 100 AND 599
        )
);

-- 4. Structured weather observations
CREATE TABLE IF NOT EXISTS fact_weather_observation (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    city_id INTEGER NOT NULL
        REFERENCES dim_city(city_id),
    observed_at TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    temperature_c NUMERIC(5, 2),
    humidity_pct NUMERIC(5, 2),
    precipitation_mm NUMERIC(8, 2),
    wind_speed_kmh NUMERIC(7, 2),
    weather_code INTEGER,
    source TEXT NOT NULL DEFAULT 'open-meteo',

    CONSTRAINT uq_city_observation
        UNIQUE (city_id, observed_at),
    CONSTRAINT chk_humidity
        CHECK (
            humidity_pct IS NULL
            OR humidity_pct BETWEEN 0 AND 100
        ),
    CONSTRAINT chk_precipitation
        CHECK (
            precipitation_mm IS NULL
            OR precipitation_mm >= 0
        ),
    CONSTRAINT chk_wind_speed
        CHECK (
            wind_speed_kmh IS NULL
            OR wind_speed_kmh >= 0
        )
);

-- Index for time-based queries
CREATE INDEX IF NOT EXISTS idx_weather_observed_at
    ON fact_weather_observation (observed_at);

CREATE INDEX IF NOT EXISTS idx_weather_city_time
    ON fact_weather_observation (city_id, observed_at DESC);

-- 5. Daily analytical mart
CREATE TABLE IF NOT EXISTS mart_daily_weather (
    city_id INTEGER NOT NULL
        REFERENCES dim_city(city_id),
    weather_date DATE NOT NULL,
    avg_temperature_c NUMERIC(5, 2),
    min_temperature_c NUMERIC(5, 2),
    max_temperature_c NUMERIC(5, 2),
    avg_humidity_pct NUMERIC(5, 2),
    total_precipitation_mm NUMERIC(10, 2),
    observation_count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (city_id, weather_date),

    CONSTRAINT chk_observation_count
        CHECK (observation_count >= 0)
);

-- Seed five Indian cities
INSERT INTO dim_city
    (city_name, latitude, longitude, timezone)
VALUES
    ('Delhi', 28.613900, 77.209000, 'Asia/Kolkata'),
    ('Mumbai', 19.076000, 72.877700, 'Asia/Kolkata'),
    ('Bengaluru', 12.971600, 77.594600, 'Asia/Kolkata'),
    ('Hyderabad', 17.385000, 78.486700, 'Asia/Kolkata'),
    ('Chennai', 13.082700, 80.270700, 'Asia/Kolkata')
ON CONFLICT (city_name) DO NOTHING;
