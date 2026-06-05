

--create type season_stats as (
--	season INTEGER,
--	gp INTEGER,
--	pts FLOAT,
--	reb real,
--	ast FLOAT
--
--);
--
--create type scoring_class as enum ('star','good','average','bad');
--DROP TABLE IF EXISTS players;
--CREATE TABLE players (
--    player_name TEXT,
--    height TEXT,
--    college TEXT,
--    country TEXT,
--    draft_year TEXT,
--    draft_round TEXT,
--    draft_number TEXT,
--    season_stats season_stats[],
--    scoring_class scoring_class,
--    years_since_last_active INTEGER,
--    is_active BOOLEAN,
--    season INTEGER,
--    
--    PRIMARY KEY (player_name, season)
--);
--
--
--
--INSERT INTO players
--WITH years AS (
--    SELECT *
--    FROM GENERATE_SERIES(1996, 2022) AS season
--), p AS (
--    SELECT
--        player_name,
--        MIN(season) AS first_season
--    FROM player_seasons
--    GROUP BY player_name
--), players_and_seasons AS (
--    SELECT *
--    FROM p
--    JOIN years y
--        ON p.first_season <= y.season
--), windowed AS (
--    SELECT
--        pas.player_name,
--        pas.season,
--        ARRAY_REMOVE(
--            ARRAY_AGG(
--                CASE
--                    WHEN ps.season IS NOT NULL
--                        THEN ROW(
--                            ps.season,
--                            ps.gp,
--                            ps.pts,
--                            ps.reb,
--                            ps.ast
--                        )::season_stats
--                END)
--            OVER (PARTITION BY pas.player_name ORDER BY COALESCE(pas.season, ps.season)),
--            NULL
--        ) AS seasons
--    FROM players_and_seasons pas
--    LEFT JOIN player_seasons ps
--        ON pas.player_name = ps.player_name
--        AND pas.season = ps.season
--    ORDER BY pas.player_name, pas.season
--), static AS (
--    SELECT
--        player_name,
--        MAX(height) AS height,
--        MAX(college) AS college,
--        MAX(country) AS country,
--        MAX(draft_year) AS draft_year,
--        MAX(draft_round) AS draft_round,
--        MAX(draft_number) AS draft_number
--    FROM player_seasons
--    GROUP BY player_name
--)
--SELECT
--    w.player_name,
--    s.height,
--    s.college,
--    s.country,
--    s.draft_year,
--    s.draft_round,
--    s.draft_number,
--    seasons AS season_stats,
--    CASE
--        WHEN (seasons[CARDINALITY(seasons)]::season_stats).pts > 20 THEN 'star'
--        WHEN (seasons[CARDINALITY(seasons)]::season_stats).pts > 15 THEN 'good'
--        WHEN (seasons[CARDINALITY(seasons)]::season_stats).pts > 10 THEN 'average'
--        ELSE 'bad'
--    END::scoring_class AS scoring_class,
--    w.season - (seasons[CARDINALITY(seasons)]::season_stats).season as years_since_last_active,
--    (seasons[CARDINALITY(seasons)]::season_stats).season = season AS is_active,
--    w.season
--FROM windowed w
--JOIN static s
--    ON w.player_name = s.player_name;
--create table player_scd (
--	player_name text,
--	scoring_class scoring_class,
--	isactive boolean,
--	start_season Integer,
--	end_season integer,
--	current_season integer,
--	primary key(player_name,start_season)
--)
insert into player_scd
with with_previous as (
select player_name ,season,scoring_class,
LAG(scoring_class,1) over (partition by player_name order by season) as previous_scoring_class,
is_active,
LAG(is_active,1) over (partition by player_name order by season) as previous_is_active
from players
where season<=2021),

with_indicators as (
select *,
	  	case 
	  		when scoring_class <> previous_scoring_class then 1
	  		
	  		when is_active <> previous_is_active then 1 
			else 0
	  	end as change_indicator
from with_previous)

, with_streaks as(
select
	*,
	SUM(change_indicator) over (partition by player_name order by season ) as streak_identifier
from
	with_indicators

)
	  	
select player_name,
scoring_class,
is_active,
MIN(season) as start_season,
MAX(season) as end_season,
2021 as current_season
from with_streaks 
group by player_name,streak_identifier, is_active,scoring_class
order by player_name,start_season;





--select player_name,scoring_class,is_active from players where season = 2022;




