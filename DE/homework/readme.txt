# Dimensional Data Modeling: Slowly Changing Dimensions (Type 2)

## 📌 Project Overview
This project demonstrates advanced dimensional data modeling techniques using PostgreSQL. The objective is to transform a raw `actor_films` dataset into a scalable, easily queryable architecture that tracks historical state changes over time using **Slowly Changing Dimensions (SCD) Type 2**.

## 🏗️ Architecture & Concepts Demonstrated

### 1. Cumulative Table Design (`actors`)
Instead of keeping a flat, highly denormalized table with massive redundancy, this pipeline leverages **Struct Arrays** (`film_info[]`). 
* **What it does:** Aggregates an actor's entire filmography into a single array column, keeping the table grain strictly at the `actor_id` level.
* **Why it matters:** This drastically reduces the number of rows the database needs to scan while preserving all historical transactional details inside the array. 

### 2. Slowly Changing Dimension Type 2 (`actors_history_scd`)
Actors' careers change over time—they take breaks, and their average ratings fluctuate. This project builds a historical tracking table to capture these states.
* **What it does:** Uses `start_date` and `end_date` columns to create a continuous historical timeline of an actor's `quality_class` (Star, Good, Average, Bad) and `is_active` status. 
* **Why it matters:** It enables point-in-time analytical querying (e.g., "Show me all actors who were classified as 'Stars' specifically between 1970 and 1973").

### 3. Streak Identification & Window Functions
* **What it does:** Uses advanced SQL window functions (`LAG`, `SUM`) to identify "streaks" of unchanged behavior. If an actor remains a "Star" for 3 consecutive years, the pipeline automatically groups those years into a single historical record.

### 4. Incremental Loading Logic
* **What it does:** Efficiently merges new daily/yearly data with historical data using `FULL OUTER JOIN` (for the cumulative table) and conditional array unnesting (for the SCD table).
* **Why it matters:** In a production environment, you cannot afford to drop and recreate massive tables every day. This pipeline is built to append and update only what has changed.