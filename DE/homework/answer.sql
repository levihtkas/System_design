/* ====================================================================
   PART 1: DATA TYPES & TABLE DEFINITIONS (DDL)
   ==================================================================== */

-- Drop existing structures if re-running
DROP TABLE IF EXISTS actors_history_scd;
DROP TABLE IF EXISTS actors;
DROP TYPE IF EXISTS film_info;

-- Create a custom data type to store film details inside an array.
-- WHY: This allows us to keep the actor table at the 'actor' grain 
-- while preserving all individual movie details.
CREATE TYPE film_info AS (
    film TEXT,
    votes INTEGER,
    rating NUMERIC,
    filmid TEXT
);

-- Create the Cumulative Actors Table
CREATE TABLE actors (
    actorid TEXT,
    films film_info[],
    quality_class TEXT,
    isactive BOOLEAN,
    current_year INTEGER,
    PRIMARY KEY (actorid, current_year)
);

/* ====================================================================
   PART 2: CUMULATIVE TABLE INCREMENTAL LOAD
   ==================================================================== */

BEGIN;

-- Remove any existing data for the target year to ensure idempotency
DELETE FROM actors WHERE current_year = 1970; 

-- Insert the merged historical and new data
INSERT INTO actors
WITH history_data AS (
    -- Get the state of the actors up to the previous year
    SELECT * FROM actors WHERE current_year = 1969
),
current_data AS (
    -- Aggregate the new year's data into arrays and calculate the new quality class
    SELECT
        actorid AS actor_id,
        ARRAY_AGG(ROW(film, votes, rating, filmid)::film_info) AS films,
        CASE
            WHEN AVG(rating) > 8 THEN 'star'
            WHEN AVG(rating) > 7 THEN 'good'
            WHEN AVG(rating) > 6 AND AVG(rating) <= 7 THEN 'average'
            ELSE 'bad'
        END AS quality_class,
        year AS current_year
    FROM actor_films 
    WHERE year = 1970
    GROUP BY actorid, year
)
-- Merge history and current data using FULL OUTER JOIN to capture
-- existing actors, completely new actors, and actors who took the year off.
SELECT
    COALESCE(cd.actor_id, hd.actorid) AS actor_id,
    CASE 
        WHEN hd.films IS NULL THEN cd.films           -- Brand new actor
        ELSE hd.films || cd.films                     -- Existing actor (concatenate arrays)
    END AS films,
    COALESCE(cd.quality_class, hd.quality_class) AS quality_class, -- Carry forward status if inactive
    CASE 
        WHEN cd.current_year IS NOT NULL THEN TRUE    -- Made a movie this year
        ELSE FALSE                                    -- Did not make a movie
    END AS isactive,
    COALESCE(cd.current_year, hd.current_year + 1) AS current_year
FROM history_data hd
FULL OUTER JOIN current_data cd 
    ON hd.actorid = cd.actor_id;

COMMIT;

/* ====================================================================
   PART 3: SCD TYPE 2 TABLE CREATION & BACKFILL
   ==================================================================== */

-- Create the Historical Slowly Changing Dimension (SCD) Table
CREATE TABLE actors_history_scd (
    actorid TEXT,
    films film_info[],
    quality_class TEXT,
    is_active BOOLEAN,
    start_date INTEGER,
    end_date INTEGER,
    PRIMARY KEY (actorid, start_date)
);

-- Backfill the entire history table using Streak Logic
INSERT INTO actors_history_scd
WITH actor_scd AS (
    -- Step 1: Use LAG to look at the previous year's state for each actor
    SELECT 
        actorid,
        films,
        quality_class,
        LAG(quality_class, 1) OVER(PARTITION BY actorid ORDER BY current_year) AS quality_class_lag,
        isactive,
        LAG(isactive, 1) OVER(PARTITION BY actorid ORDER BY current_year) AS is_active_lag,
        current_year AS start_date,
        current_year + 1 AS end_date
    FROM actors 
), 
indicators AS (
    -- Step 2: Flag a '1' every time the state changes, '0' if it stays the same
    SELECT *, 
        CASE
            WHEN quality_class <> quality_class_lag OR isactive <> is_active_lag THEN 1
            ELSE 0
        END AS change_indicators
    FROM actor_scd
), 
with_streaks AS (
    -- Step 3: Create a unique streak ID by taking a cumulative sum of the change flags
    SELECT *, 
        SUM(change_indicators) OVER(PARTITION BY actorid ORDER BY start_date) AS streak_identifier 
    FROM indicators 
)
-- Step 4: Group by the streak ID to collapse continuous years into single historical records
SELECT 
    actorid,
    films,
    quality_class,
    isactive,
    MIN(start_date) AS start_date,
    MAX(end_date) AS end_date
FROM with_streaks 
GROUP BY actorid, films, streak_identifier, quality_class, isactive 
ORDER BY actorid, start_date;

/* ====================================================================
   PART 4: SCD TYPE 2 INCREMENTAL UPDATE LOGIC
   ==================================================================== */

-- This query demonstrates how to process a single new year of data 
-- against the existing historical SCD table without rebuilding it from scratch.

WITH historical_scd AS (
    -- Get the currently open historical records (where streak hasn't ended)
    SELECT actorid, films, quality_class, is_active, start_date 
    FROM actors_history_scd 
    WHERE end_date < 1975
),
current_records AS (
    -- Get the brand new incoming data
    SELECT * FROM actors WHERE current_year = 1974
),
unchanged_records AS (
    -- Logic for actors whose status did NOT change (extend their streak)
    SELECT 
        cr.actorid,
        CASE
            WHEN cr.films IS NULL THEN hs.films
            ELSE hs.films || cr.films
        END AS films,
        hs.quality_class,
        hs.is_active,
        hs.start_date
    FROM historical_scd hs 
    INNER JOIN current_records cr 
        ON hs.actorid = cr.actorid 
    WHERE cr.quality_class = hs.quality_class AND cr.isactive = hs.is_active 
),
new_and_changed_records AS (
    -- Logic for brand new actors OR actors whose status DID change
    -- Utilizing a LEFT JOIN to capture both scenarios in one pass
    SELECT 
        cd.actorid,
        CASE
            WHEN hs.films IS NULL THEN cd.films        -- New actor
            ELSE hs.films || cd.films                  -- Changed actor
        END AS films,
        cd.quality_class,
        cd.isactive,
        cd.current_year 
    FROM current_records cd 
    LEFT JOIN historical_scd hs 
        ON cd.actorid = hs.actorid 
)
-- Combine all the logic into a single output
SELECT * FROM historical_scd
UNION ALL
SELECT * FROM unchanged_records
UNION ALL
SELECT * FROM new_and_changed_records;