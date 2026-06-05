
--create table player_scd (
--	player_name text,
--	scoring_class scoring_class,
--	isactive boolean,
--	start_season Integer,
--	end_season integer,
--	current_season integer,
--	primary key(player_name,current_season)
--)

with with_previous as(
select
	player_name,
	season,
	scoring_class,
	lag(scoring_class, 1) over(partition by player_name order by season) as previous_scoring_class,
	is_active, 
	lag(is_active, 1) over(partition by player_name order by season ) as previous_isactive
from
	players
order by
	player_name 
),

with_indicators as (
select *,
case
	when scoring_class <> previous_scoring_class then 1
	when is_active <> previous_isactive then 1
	else 0
end as change_indicator
from with_previous

)

select *, SUM(change_indicator) over(partition by player_name order by season) as streak_identifier from with_indicators;

select * from player_scd;