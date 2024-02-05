use database hackathon;
use schema group_1;

-- copy data source
create or replace table draft_lp_ce_estimates_2024
as select * from data_source.commencing_estimates.draft_lp_ce_estimates_2024;


-- rule tables
insert into rule_annual_increase (default_annual_increase) values (0.03);

-- load reference tables
-- stage data source
create or replace table stage_data_source as
select scenario_type,
       period_name,
       course_name,
       owning_faculty,
       commencing_study_period,
       course_level_name,
       fee_liability_group,
       sum(course_enrolment_count) as course_enrolment_count
from draft_lp_ce_estimates_2024
where scenario_type in ('Final', '2023 Budget', '2023 CD1R', '2024 Load Plan 1.0', '2024 Load Plan 2.0')
  and (period_name in ('2023', '2024', '2025', '2026', '2027', '2028') or period_name like '%Final')
group by scenario_type,
         period_name,
         course_name,
         owning_faculty,
         commencing_study_period,
         course_level_name,
         fee_liability_group
;

insert overwrite into ref_course (course_name, owning_faculty_id)
with course as
(
    select course_name, owning_faculty
    from stage_data_source
    qualify row_number() over (partition by course_name order by period_name desc) = 1
)
select course.course_name, ref_owning_faculty.id
from course
inner join ref_owning_faculty
    on ref_owning_faculty.faculty_name=course.owning_faculty
;

insert overwrite into ref_period (period_name)
select distinct period_name from stage_data_source;
;

insert overwrite into ref_owning_faculty (faculty_name)
(
select distinct owning_faculty from stage_data_source
);

insert overwrite into ref_course_level (course_level_name)
select distinct course_level_name from stage_data_source;

insert overwrite into ref_commencing_study_period (commencing_study_period)
select distinct commencing_study_period from stage_data_source;

insert overwrite into ref_fee_liability_group (fee_liability_group, fee_liability_group_type)
with fee_liability_group as (
select distinct fee_liability_group,
    case when fee_liability_group ilike '%international%' then 'International' else 'Domestic' end as fee_liaility_group_type
from stage_data_source
)
select * from fee_liability_group;


insert overwrite into scenario (scenario_name, version_name, notes, is_final, confirmed_by_arts,
confirmed_by_mqbs, confirmed_by_sci, confirmed_by_fmhhs)
select distinct scenario_type, 'final version', scenario_type, 'Y','Y','Y','Y', 'Y'
from stage_data_source
where scenario_type in ('2024 Load Plan 1.0', '2024 Load Plan 2.0');

-- load 2024 actuals



