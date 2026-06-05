--SELECT * FROM player_seasons;
--
--create type seasons_stats as (
--	season INTEGER,
--	gp INTEGER,
--	pts FLOAT,
--	reb real,
--	ast FLOAT
--
--)
--
--
--create type scoringClass as enum ('star','good','average','bad');
--
--DROP TABLE IF EXISTS players;
--create table players (
--	player_name TEXT,
--	height TEXT,
--	college text,
--	country text,
--	draft_year text,
--	draft_round text,
--	draft_number text,
--	season_stats seasons_stats[],
--	current_season INTEGER,
--	scores scoringClass,
--	years_since_last_season INTEGER,
--	primary key (player_name,current_season)
--);
-- 

insert into players
with yesterday as (
select
	*
from
	players
where
	current_season = 2000
),
today as (
select
	*
from
	player_seasons ps
where
	season = 2001
)

select
	coalesce(t.player_name, y.player_name) as PLAYER_NAME,
	coalesce(t.height, y.height) as height,
	coalesce(t.college, y.college) as college,
	coalesce(t.country, y.country) as country,
	coalesce(t.draft_year, y.draft_year) as draft_year,
	coalesce(t.draft_round, y.draft_round) as draft_round,
	coalesce(t.draft_number, y.draft_number) as draft_number,
	case when y.season_stats is null
then array[row(
t.season,
t.gp, t.pts, t.reb, t.ast
):: seasons_stats]
		when t.season is not null then y.season_stats || array[row(
t.season,
t.gp, t.pts, t.reb, t.ast
):: seasons_stats]
		else y.season_stats
	end as season_stats,
	coalesce(t.season, y.current_season + 1) as current_season,
	case
		when t.season is not null then
		case when t.pts > 20 then 'star'
			when t.pts >10 then 'good'
			else 'average'
		end :: scoringClass
		else y.scores
	end as scores,
	case when t.season is not null then 0
	else y.years_since_last_season+1
	end as years_since_last_season
	from
	today t
full outer join yesterday y on
	t.player_name = y.player_name;

select
	player_name ,
	season_stats [1] as fitst_season,
	season_stats[cardinality(season_stats)].pts / case
		when season_stats[1].pts = 0.0 then 1.0
		else season_stats[1].pts
	end as pts_avg,
	season_stats[cardinality(season_stats)].pts as latest_pts
from
	players
where
	player_name like "%Michael Jordan" order by pts_avg DESC;

 