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
-- 2024.march actuals
-- apply random float between 0.8 to 1.2 on the course enrolments from '2024 Load Plan 2.0', 2024.Session_1
create or replace table commence_actual as
with base as (
    select scenario_type,
        period_name,
        course_name,
        owning_faculty,
        commencing_study_period,
        course_level_name,
        fee_liability_group,
        sum(course_enrolment_count) as course_enrolment_count
    from draft_lp_ce_estimates_2024
    where scenario_type in ('2024 Load Plan 2.0')
        and period_name in ('2024')
        and commencing_study_period in ('Session 1')
    group by scenario_type,
        period_name,
        course_name,
        owning_faculty,
        commencing_study_period,
        course_level_name,
        fee_liability_group
)
select '2024.03' as actual_name,
    '2024' period_name,
    commencing_study_period,
    course_name,
    owning_faculty,
    course_level_name,
    fee_liability_group,
    ceil(uniform(0.8::float, 1.2::float, random(4321))*course_enrolment_count) as course_enrolment_count
from base
;

-- apply random float between 0.8 to 1.2 on the course enrolments from '2024 Load Plan 2.0', 2024.Session_2
insert into commence_actual
with session_1 as (
    select '2024.07' as actual_name,
        '2024' as period_name,
        commencing_study_period,
        course_name,
        owning_faculty,
        course_level_name,
        fee_liability_group,
        course_enrolment_count
    from commence_actual
),
session_2 as (

    with base as (
        select scenario_type,
            period_name,
            course_name,
            owning_faculty,
            commencing_study_period,
            course_level_name,
            fee_liability_group,
            sum(course_enrolment_count) as course_enrolment_count
        from draft_lp_ce_estimates_2024
        where scenario_type in ('2024 Load Plan 2.0')
            and period_name in ('2024')
            and commencing_study_period in ('Session 2')
        group by scenario_type,
        period_name,
        course_name,
        owning_faculty,
        commencing_study_period,
        course_level_name,
        fee_liability_group
    )
    select '2024.07' as actual_name,
        '2024' period_name,
        commencing_study_period,
        course_name,
        owning_faculty,
        course_level_name,
        fee_liability_group,
        ceil(uniform(0.8::float, 1.2::float, random(4321))*course_enrolment_count) as course_enrolment_count
    from base

),
session_union as (
    select * from session_1
    union all
    select * from session_2
)

select * from session_union
;

insert into scenario_data (
    scenario_id,
    course,
    period,
    commencing_study_period,
    owning_faculty_name,
    course_level_name,
    fee_liability_group,
    course_enrolment_count
)
select scenario.id as scenario_id,
    ds.course_name ,
    ds.period_name,
    ds.commencing_study_period,
    ds.owning_faculty,
    ds.course_level_name,
    ds.fee_liability_group,
    ds.course_enrolment_count
from stage_data_source as ds
inner join scenario on scenario.scenario_name=ds.scenario_type
inner join ref_course on ref_course.course_name=ds.course_name
inner join ref_period on ref_period.period_name=ds.period_name
inner join ref_owning_faculty on ref_owning_faculty.faculty_name=ds.owning_faculty
inner join ref_course_level on ref_course_level.course_level_name=ds.course_level_name
inner join ref_fee_liability_group on ref_fee_liability_group.fee_liability_group=ds.fee_liability_group
where 1=1
;

