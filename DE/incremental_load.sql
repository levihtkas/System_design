--CREATE TYPE scd_type AS (
--    scoring_class scoring_class,
--    is_active boolean,
--    start_season integer,
--    end_season integer
--);

with last_season_scd as (
	select * from player_scd ps
	where current_season = 2021 and end_season = 2021
), -- BUCKET 1 : get everyone who has currently active at end of 2021
this_season_data as (
	select * from players where season=2022
), -- brand new data 2022
historical_scd as (
	select player_name,scoring_class,isactive ,start_season ,end_season  from player_scd where current_season = 2021 and end_season<2021
), -- streaks end before 2021
unchanged_records as (
select ts.player_name,ls.scoring_class,ls.isactive,ls.start_season ,ts.season as end_season  
from this_season_data ts
join last_season_scd ls
on ts.player_name = ls.player_name 
where ts.scoring_class = ls.scoring_class  and ts.is_active = ls.isactive 
) -- exact same just stretch end_season
,
changed_records as (
	select 
	ts.player_name ,
	UNNEST(
	ARRAY[
	ROW(
	ls.scoring_class,
    ls.isactive,
    ls.start_season,
    ls.end_season)::scd_type,
	ROW(
	ts.scoring_class,
    ts.is_active,
    ts.season,
    ts.season
	)::scd_type
	]
	) as records
	from this_season_data ts
	left join last_season_scd ls
	on ls.player_name = ts.player_name 
	where (ts.scoring_class <> ls.scoring_class or ts.is_active <> ls.isactive)

),
unnested_changed_records as (
	select player_name,
		(records).scoring_class,
        (records).is_active,
        (records).start_season,
        (records).end_season
    FROM changed_records
),
new_records as (
	select ts.player_name,
		ts.scoring_class,
		ts.is_active,
		ts.season as start_season,
		ts.season as end_season
	from this_season_data ts left join last_season_scd ls
	on ts.player_name = ls.player_name
	where ls.player_name is null
)

select * from historical_scd

union all 

select * from unchanged_records
union all
select * from unnested_changed_records

union all 
select * from new_records;
